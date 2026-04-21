#!/usr/bin/env python3
"""active_decisions.py — currently-active decision-made entries for a project.

A `decision-made` is **active** unless it has been retired by a later
`decision-made` whose `retires` array contains its ID. This script does the
set-subtraction so callers don't have to.

Usage:
    active_decisions.py --project <slug> [--since YYYY-MM-DD] [--limit N]

Output (stdout, JSON): list of active decisions, newest first.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, iter_jsonl, parse_kst, project_root  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Active decisions for a project.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    ap.add_argument("--since", help="Only return decisions on/after this date (YYYY-MM-DD)")
    ap.add_argument("--limit", type=int, default=None)
    args = ap.parse_args()

    proj = project_root(args.project, args.path)
    dec_path = proj / "decisions.jsonl"

    made: dict[str, dict] = {}
    retired: set[str] = set()
    for entry in iter_jsonl(dec_path):
        if entry.get("type") != "decision-made":
            continue
        ident = entry.get("id")
        if not isinstance(ident, str):
            continue
        made[ident] = entry
        for rid in entry.get("retires", []) or []:
            if isinstance(rid, str):
                rid_clean = rid.strip("[]")
                if rid_clean.startswith("dec-"):
                    retired.add(rid_clean)

    cutoff = parse_kst(args.since) if args.since else None

    active = []
    for ident, entry in made.items():
        if ident in retired:
            continue
        when = parse_kst(str(entry.get("when") or ""))
        if cutoff and when and when < cutoff:
            continue
        active.append({
            "id": ident,
            "when": entry.get("when"),
            "decision": entry.get("decision"),
            "context": entry.get("context"),
            "from": entry.get("from"),
            "links": entry.get("links"),
            "who": entry.get("who"),
        })

    active.sort(key=lambda d: d.get("when") or "", reverse=True)
    if args.limit:
        active = active[: args.limit]

    emit({
        "project": proj.name,
        "count": len(active),
        "decisions": active,
    })


if __name__ == "__main__":
    main()
