#!/usr/bin/env python3
"""meeting_context.py — prior context bundle for a new meeting MD.

Used by the `meeting` skill before generating a meeting MD: collect prior
project state relevant to the upcoming meeting, so Claude can frame the
new meeting in continuity with what came before.

Usage:
    meeting_context.py --project <slug> [--attendees name1 name2 ...] \\
                       [--lookback-days 14] [--max-items 8]

Output (stdout, JSON): bundle of prior meetings, recent decisions made,
pending raised decisions, open risks, attendee-tagged actions.
"""
from __future__ import annotations

import argparse
import sys
from datetime import timedelta
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    emit,
    iter_jsonl,
    load_frontmatter,
    now_kst,
    now_kst_str,
    parse_kst,
    project_root,
)


def main() -> None:
    ap = argparse.ArgumentParser(description="Prior context for a meeting.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path (overrides --project)")
    ap.add_argument("--attendees", nargs="*", default=[])
    ap.add_argument("--lookback-days", type=int, default=14)
    ap.add_argument("--max-items", type=int, default=8)
    args = ap.parse_args()

    proj = project_root(args.project, args.path)
    cutoff = now_kst() - timedelta(days=args.lookback_days)

    # 1. Prior meetings (MD frontmatter).
    meetings = []
    meetings_dir = proj / "meetings"
    if meetings_dir.is_dir():
        for md in sorted(meetings_dir.glob("*.md")):
            meta, _ = load_frontmatter(md)
            when = parse_kst(str(meta.get("when") or ""))
            if when and when >= cutoff:
                meetings.append({
                    "id": meta.get("id"),
                    "title": meta.get("title"),
                    "when": str(meta.get("when")),
                    "type": meta.get("type"),
                    "path": str(md.relative_to(proj)),
                })
    meetings = meetings[-args.max_items:]

    # 2. Recent decisions made + currently raised.
    dec_path = proj / "core" / "decisions.jsonl"
    recent_made = []
    raised_open: list[dict] = []
    raised: dict[str, dict] = {}
    closed_ids: set[str] = set()
    for entry in iter_jsonl(dec_path):
        t = entry.get("type")
        when = parse_kst(str(entry.get("when") or ""))
        if t == "decision-raised":
            raised[entry.get("id")] = entry
        elif t in ("decision-made", "decision-dropped"):
            frm = entry.get("from")
            if isinstance(frm, str) and frm.startswith("[dec-"):
                closed_ids.add(frm.strip("[]"))
            if t == "decision-made" and when and when >= cutoff:
                recent_made.append({
                    "id": entry.get("id"),
                    "decision": entry.get("decision"),
                    "when": entry.get("when"),
                })
    for rid, entry in raised.items():
        if rid not in closed_ids:
            raised_open.append({
                "id": rid,
                "question": entry.get("question"),
                "when": entry.get("when"),
            })

    # 3. Open risks (when_resolved empty).
    open_risks = []
    risks_dir = proj / "risks"
    if risks_dir.is_dir():
        for md in risks_dir.glob("*.md"):
            meta, _ = load_frontmatter(md)
            if not meta.get("when_resolved"):
                open_risks.append({
                    "id": meta.get("id"),
                    "title": meta.get("title"),
                    "category": meta.get("category"),
                    "who": meta.get("who"),
                    "when_surfaced": meta.get("when_surfaced"),
                    "path": str(md.relative_to(proj)),
                })

    # 4. Attendee-tagged open tasks.
    attendee_set = {a.lower() for a in args.attendees}
    tasks = []
    if attendee_set:
        act_path = proj / "core" / "actions.jsonl"
        completed_from: set[str] = set()
        all_tasks: dict[str, dict] = {}
        for entry in iter_jsonl(act_path):
            t = entry.get("type")
            if t == "task-created":
                all_tasks[entry.get("id")] = entry
            elif t in ("task-done", "task-blocked"):
                frm = entry.get("from")
                if isinstance(frm, str) and frm.startswith("[act-") and t == "task-done":
                    completed_from.add(frm.strip("[]"))
        for tid, entry in all_tasks.items():
            if tid in completed_from:
                continue
            who = str(entry.get("who") or "").lower()
            if who in attendee_set:
                tasks.append({
                    "id": tid,
                    "what": entry.get("what"),
                    "who": entry.get("who"),
                    "when": entry.get("when"),
                })

    emit({
        "project": str(proj.name),
        "as_of": now_kst_str(),
        "lookback_days": args.lookback_days,
        "prior_meetings": meetings,
        "recent_decisions_made": recent_made[: args.max_items],
        "open_raised_decisions": raised_open[: args.max_items],
        "open_risks": open_risks[: args.max_items],
        "attendee_open_tasks": tasks[: args.max_items],
    })


if __name__ == "__main__":
    main()
