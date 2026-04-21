#!/usr/bin/env python3
"""frontmatter_index.py — index of MD frontmatter in a folder.

Usage:
    frontmatter_index.py <folder> [--field name1 name2 ...] [--filter k=v ...]

Output (stdout, JSON): list of {path, frontmatter_subset, ...}.

Notes:
    - --field restricts the output frontmatter to just those keys.
    - --filter applies AND-matching on string equality (e.g. status=active).
    - Body is never returned; this is a lightweight index, not a content dump.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, fail, load_frontmatter  # noqa: E402


def parse_filters(items: list[str]) -> list[tuple[str, str]]:
    out = []
    for item in items:
        if "=" not in item:
            fail(f"--filter expects key=value, got: {item}")
        k, v = item.split("=", 1)
        out.append((k.strip(), v.strip()))
    return out


def matches(meta: dict, filters: list[tuple[str, str]]) -> bool:
    for k, v in filters:
        if str(meta.get(k, "")).strip() != v:
            return False
    return True


def main() -> None:
    ap = argparse.ArgumentParser(description="Index MD frontmatter in a folder.")
    ap.add_argument("folder")
    ap.add_argument("--field", nargs="*", default=None,
                    help="Restrict output to these frontmatter keys")
    ap.add_argument("--filter", nargs="*", default=[],
                    help="AND-filters as key=value")
    ap.add_argument("--recursive", action="store_true")
    args = ap.parse_args()

    folder = Path(args.folder)
    if not folder.is_dir():
        fail(f"folder does not exist: {folder}")

    filters = parse_filters(args.filter)
    pattern = "**/*.md" if args.recursive else "*.md"

    out = []
    for md in sorted(folder.glob(pattern)):
        meta, _ = load_frontmatter(md)
        if filters and not matches(meta, filters):
            continue
        if args.field:
            entry = {k: meta.get(k) for k in args.field}
        else:
            entry = dict(meta)
        entry["_path"] = str(md)
        out.append(entry)

    emit({"folder": str(folder), "count": len(out), "entries": out})


if __name__ == "__main__":
    main()
