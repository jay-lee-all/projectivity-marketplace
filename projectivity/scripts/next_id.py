#!/usr/bin/env python3
"""next_id.py — return the next sequential ID for a given prefix.

Usage:
    next_id.py --jsonl <path>                  # for dec- / act- in JSONL
    next_id.py --folder <path> --prefix req-   # for req- / meet- / risk- in MD frontmatter

Output (stdout, JSON):
    {"prefix": "dec-", "next": "dec-042", "last": "dec-041"}

Notes:
    - Sequential NNN is zero-padded to 3 digits (widens to 4 automatically at 1000).
    - JSONL mode scans every line's "id" field; MD mode scans frontmatter "id".
    - Gaps are ignored — we hand out last+1. Reclaiming gaps would undermine
      append-only provenance.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked
# (direct `python scripts/next_id.py`, `python -m`, or from an unrelated cwd).
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, fail, iter_jsonl, load_frontmatter  # noqa: E402


ID_RE = re.compile(r"^([a-z]+-)(\d{3,5})$")


def scan_jsonl(path: Path) -> tuple[str | None, str | None]:
    max_n = -1
    prefix = None
    last = None
    for obj in iter_jsonl(path):
        ident = obj.get("id")
        if not isinstance(ident, str):
            continue
        m = ID_RE.match(ident)
        if not m:
            continue
        p, n = m.group(1), int(m.group(2))
        if prefix is None:
            prefix = p
        if n > max_n:
            max_n = n
            last = ident
    return prefix, last


def scan_md_folder(folder: Path, prefix: str) -> str | None:
    max_n = -1
    last = None
    for md in folder.glob("*.md"):
        meta, _ = load_frontmatter(md)
        ident = meta.get("id")
        if not isinstance(ident, str) or not ident.startswith(prefix):
            continue
        m = ID_RE.match(ident)
        if not m:
            continue
        n = int(m.group(2))
        if n > max_n:
            max_n = n
            last = ident
    return last


def next_from(last: str | None, prefix: str) -> str:
    if last is None:
        return f"{prefix}001"
    m = ID_RE.match(last)
    if not m:
        fail(f"malformed last id: {last}")
    n = int(m.group(2)) + 1
    width = max(3, len(m.group(2)))
    return f"{prefix}{n:0{width}d}"


def main() -> None:
    ap = argparse.ArgumentParser(description="Return next sequential ID.")
    ap.add_argument("--jsonl", help="JSONL file to scan (dec- / act-)")
    ap.add_argument("--folder", help="MD folder to scan (req- / meet- / risk-)")
    ap.add_argument("--prefix", help="Prefix override (required for --folder)")
    args = ap.parse_args()

    if args.jsonl and args.folder:
        fail("use --jsonl OR --folder, not both")

    if args.jsonl:
        path = Path(args.jsonl)
        if not path.exists():
            # First write into this file: bootstrap.
            prefix = args.prefix or ""
            if not prefix:
                fail("--prefix required when --jsonl does not yet exist")
            emit({"prefix": prefix, "last": None, "next": f"{prefix}001"})
            return
        prefix, last = scan_jsonl(path)
        if prefix is None:
            prefix = args.prefix or ""
            if not prefix:
                fail("no ids in JSONL and no --prefix given")
        emit({"prefix": prefix, "last": last, "next": next_from(last, prefix)})
        return

    if args.folder:
        if not args.prefix:
            fail("--prefix is required with --folder")
        folder = Path(args.folder)
        if not folder.is_dir():
            fail(f"folder does not exist: {folder}")
        last = scan_md_folder(folder, args.prefix)
        emit({"prefix": args.prefix, "last": last, "next": next_from(last, args.prefix)})
        return

    fail("one of --jsonl or --folder is required")


if __name__ == "__main__":
    main()
