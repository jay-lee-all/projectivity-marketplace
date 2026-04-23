#!/usr/bin/env python3
"""filter_by_age.py — age-aware filter over JSONL entries or MD frontmatter.

Returns entries whose dated field falls in a requested day-age window, with
`age_days` computed. Filters in addition on exact-match key=value (same
semantics as frontmatter_index.py), and in JSONL mode on --type.

Stateless — unlike aging_pending.py which is state-machine aware
(raised/made, created/done), this script just filters on age.

Usage:
    # MD folder mode (risks, requirements, meetings)
    filter_by_age.py --folder <path> --field when_surfaced \\
        [--min-days N] [--max-days M] [--filter k=v]...

    # JSONL mode (decisions.jsonl, actions.jsonl)
    filter_by_age.py --jsonl <path> --field when \\
        [--min-days N] [--max-days M] [--type <type>] [--filter k=v]...

Output (stdout, JSON): count + entries (age_days injected), sorted by age desc.
Unparseable date values are not silently dropped — they appear in `unparseable`.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    emit,
    fail,
    iter_jsonl,
    load_frontmatter,
    now_kst,
    now_kst_str,
    parse_kst,
)


def parse_filters(items: list[str]) -> list[tuple[str, str]]:
    out = []
    for item in items:
        if "=" not in item:
            fail(f"--filter expects key=value, got: {item}")
        k, v = item.split("=", 1)
        out.append((k.strip(), v.strip()))
    return out


def matches_filters(meta: dict, filters: list[tuple[str, str]]) -> bool:
    for k, v in filters:
        if str(meta.get(k, "") or "").strip() != v:
            return False
    return True


def in_age_window(age_days: int, min_days: int | None, max_days: int | None) -> bool:
    if min_days is not None and age_days < min_days:
        return False
    if max_days is not None and age_days > max_days:
        return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Filter entries by age of a dated field.")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--folder", help="MD folder to scan (frontmatter mode)")
    grp.add_argument("--jsonl", help="JSONL file to scan")

    ap.add_argument("--field", required=True,
                    help="Field holding the timestamp (e.g. when_surfaced, when)")
    ap.add_argument("--min-days", type=int, default=None,
                    help="Minimum age in days (inclusive)")
    ap.add_argument("--max-days", type=int, default=None,
                    help="Maximum age in days (inclusive)")
    ap.add_argument("--type", dest="type_filter", default=None,
                    help="JSONL mode only: require entry.type == this value")
    ap.add_argument("--filter", nargs="*", default=[],
                    help="AND-filters as key=value")
    ap.add_argument("--recursive", action="store_true",
                    help="MD folder mode only: recurse into subdirectories")
    args = ap.parse_args()

    if args.type_filter and not args.jsonl:
        fail("--type only applies with --jsonl")

    filters = parse_filters(args.filter)
    now = now_kst()
    entries: list[dict] = []
    unparseable: list[dict] = []

    if args.folder:
        folder = Path(args.folder)
        if not folder.is_dir():
            fail(f"folder does not exist: {folder}")
        pattern = "**/*.md" if args.recursive else "*.md"
        for md in sorted(folder.glob(pattern)):
            meta, _ = load_frontmatter(md)
            if filters and not matches_filters(meta, filters):
                continue
            raw = meta.get(args.field)
            raw_str = str(raw) if raw is not None else ""
            if not raw_str:
                continue
            parsed = parse_kst(raw_str)
            if parsed is None:
                unparseable.append({"_path": str(md), "field_value": raw_str})
                continue
            age = (now - parsed).days
            if not in_age_window(age, args.min_days, args.max_days):
                continue
            rec = dict(meta)
            rec["_path"] = str(md)
            rec["age_days"] = age
            entries.append(rec)

    else:  # --jsonl
        jpath = Path(args.jsonl)
        if not jpath.exists():
            fail(f"jsonl file does not exist: {jpath}")
        for entry in iter_jsonl(jpath):
            if args.type_filter and entry.get("type") != args.type_filter:
                continue
            if filters and not matches_filters(entry, filters):
                continue
            raw = entry.get(args.field)
            raw_str = str(raw) if raw is not None else ""
            if not raw_str:
                continue
            parsed = parse_kst(raw_str)
            if parsed is None:
                unparseable.append({"id": entry.get("id"), "field_value": raw_str})
                continue
            age = (now - parsed).days
            if not in_age_window(age, args.min_days, args.max_days):
                continue
            rec = dict(entry)
            rec["age_days"] = age
            entries.append(rec)

    entries.sort(key=lambda e: e.get("age_days", 0), reverse=True)

    emit({
        "source": args.folder or args.jsonl,
        "field": args.field,
        "min_days": args.min_days,
        "max_days": args.max_days,
        "type_filter": args.type_filter,
        "as_of": now_kst_str(),
        "count": len(entries),
        "entries": entries,
        "unparseable": unparseable,
    })


if __name__ == "__main__":
    main()
