#!/usr/bin/env python3
"""aging_pending.py — raised decisions older than a threshold, still open.

A `decision-raised` is open until a later `decision-made` or
`decision-dropped` entry references it via `from`.

Usage:
    aging_pending.py --project <slug> [--threshold 14] [--include-tasks]

Output (stdout, JSON): list of aging open raised decisions; optionally also
overdue task-created entries past the same threshold.
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, iter_jsonl, now_kst, now_kst_str, parse_kst, project_root  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Aging pending decisions/tasks.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    ap.add_argument("--threshold", type=int, default=14,
                    help="Days. Default 14.")
    ap.add_argument("--include-tasks", action="store_true",
                    help="Also include open task-created past threshold")
    args = ap.parse_args()

    proj = project_root(args.project, args.path)
    cutoff = now_kst() - timedelta(days=args.threshold)

    # Pending raised.
    raised: dict[str, dict] = {}
    closed: set[str] = set()
    for entry in iter_jsonl(proj / "decisions.jsonl"):
        t = entry.get("type")
        if t == "decision-raised":
            ident = entry.get("id")
            if isinstance(ident, str):
                raised[ident] = entry
        elif t in ("decision-made", "decision-dropped"):
            frm = entry.get("from")
            if isinstance(frm, str) and frm.startswith("[dec-"):
                closed.add(frm.strip("[]"))

    aging_decisions = []
    for ident, entry in raised.items():
        if ident in closed:
            continue
        when = parse_kst(str(entry.get("when") or ""))
        if when and when <= cutoff:
            age_days = (now_kst() - when).days
            aging_decisions.append({
                "id": ident,
                "question": entry.get("question"),
                "when": entry.get("when"),
                "age_days": age_days,
                "from": entry.get("from"),
                "who": entry.get("who"),
            })
    aging_decisions.sort(key=lambda d: d.get("age_days", 0), reverse=True)

    aging_tasks = []
    if args.include_tasks:
        tasks: dict[str, dict] = {}
        completed: set[str] = set()
        for entry in iter_jsonl(proj / "actions.jsonl"):
            t = entry.get("type")
            if t == "task-created":
                ident = entry.get("id")
                if isinstance(ident, str):
                    tasks[ident] = entry
            elif t == "task-done":
                frm = entry.get("from")
                if isinstance(frm, str) and frm.startswith("[act-"):
                    completed.add(frm.strip("[]"))
        for ident, entry in tasks.items():
            if ident in completed:
                continue
            when = parse_kst(str(entry.get("when") or ""))
            if when and when <= cutoff:
                aging_tasks.append({
                    "id": ident,
                    "what": entry.get("what"),
                    "who": entry.get("who"),
                    "when": entry.get("when"),
                    "age_days": (now_kst() - when).days,
                })
        aging_tasks.sort(key=lambda d: d.get("age_days", 0), reverse=True)

    out = {
        "project": proj.name,
        "threshold_days": args.threshold,
        "as_of": now_kst_str(),
        "aging_decisions": aging_decisions,
    }
    if args.include_tasks:
        out["aging_tasks"] = aging_tasks
    emit(out)


if __name__ == "__main__":
    main()
