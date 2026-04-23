#!/usr/bin/env python3
"""backfill_probe.py — compute the backfill windowing plan.

Given earliest-timestamp inputs the caller fetched via Slack/Linear MCP, this
script computes the effective since/until range (floored at overview.md's
when_created) and emits the chronological window list per the adaptive table
in curate/SKILL.md Backfill mode.

This script does NOT fetch from MCP — the caller does, and passes timestamps
in. Keeps the script deterministic and testable without live connectors.

Usage:
    backfill_probe.py --project <slug> \\
        [--slack-earliest <ts>]... \\
        [--linear-earliest <ts>] \\
        [--chosen-since <ts>] \\
        [--now <ts>]

    Timestamps: naive ISO 8601 KST (YYYY-MM-DDTHH:MM:SS) or date-only YYYY-MM-DD.

Output (stdout, JSON): effective range + window list.
"""
from __future__ import annotations

import argparse
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    KST,
    emit,
    fail,
    load_frontmatter,
    now_kst,
    now_kst_str,
    parse_kst,
    project_root,
)


def fmt(dt: datetime) -> str:
    """Canonical vault format: naive ISO 8601 KST, seconds precision."""
    return dt.astimezone(KST).strftime("%Y-%m-%dT%H:%M:%S")


def read_when_created(proj: Path) -> datetime:
    overview = proj / "overview.md"
    if not overview.exists():
        fail(f"overview.md not found: {overview}")
    meta, _ = load_frontmatter(overview)
    wc = meta.get("when_created")
    if not wc:
        fail("overview.md frontmatter missing when_created")
    parsed = parse_kst(str(wc))
    if parsed is None:
        fail(f"overview.md when_created does not parse: {wc}")
    return parsed


def pick_window_size(span_days: float, span_seconds: float) -> tuple[str, timedelta | None]:
    """Return (label, step) per the adaptive table in curate/SKILL.md.

    step=None means "single window covering the full span" (sub-2h case).
    """
    if span_seconds < 2 * 3600:
        return "single", None
    if span_seconds < 86400:
        return "hourly", timedelta(hours=1)
    if span_days < 7:
        return "daily", timedelta(days=1)
    if span_days <= 60:
        return "weekly", timedelta(days=7)
    # > 2 months: target 10–15 windows. Weekly works up to ~15 weeks; beyond
    # that, biweekly keeps the window count bounded.
    if span_days <= 15 * 7:
        return "weekly", timedelta(days=7)
    return "biweekly", timedelta(days=14)


def build_windows(since: datetime, until: datetime,
                  step: timedelta | None) -> list[dict]:
    if step is None or until <= since:
        return [{"index": 1, "since": fmt(since), "until": fmt(until)}]
    windows: list[dict] = []
    cursor = since
    idx = 1
    while cursor < until:
        nxt = min(cursor + step, until)
        windows.append({"index": idx, "since": fmt(cursor), "until": fmt(nxt)})
        cursor = nxt
        idx += 1
    return windows


def main() -> None:
    ap = argparse.ArgumentParser(description="Compute backfill windowing plan.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    ap.add_argument("--slack-earliest", action="append", default=[],
                    help="Earliest Slack message timestamp (repeatable per channel)")
    ap.add_argument("--linear-earliest", default=None,
                    help="Earliest Linear issue updated_at")
    ap.add_argument("--chosen-since", default=None,
                    help="PM-selected lower bound (overrides the probed floor)")
    ap.add_argument("--now", default=None,
                    help="Upper bound (default: current time in KST)")
    args = ap.parse_args()

    proj = project_root(args.project, args.path)
    when_created = read_when_created(proj)

    # Earliest probed timestamp across all sources (floor at when_created).
    probed: list[datetime] = []
    for ts in args.slack_earliest:
        parsed = parse_kst(ts)
        if parsed is None:
            fail(f"--slack-earliest does not parse: {ts}")
        probed.append(parsed)
    if args.linear_earliest:
        parsed = parse_kst(args.linear_earliest)
        if parsed is None:
            fail(f"--linear-earliest does not parse: {args.linear_earliest}")
        probed.append(parsed)

    earliest_probed = min(probed) if probed else when_created
    effective_floor = max(when_created, earliest_probed)

    if args.chosen_since:
        parsed = parse_kst(args.chosen_since)
        if parsed is None:
            fail(f"--chosen-since does not parse: {args.chosen_since}")
        # PM's choice is authoritative for --since, but never goes below the floor.
        effective_since = max(parsed, effective_floor)
    else:
        effective_since = effective_floor

    if args.now:
        parsed = parse_kst(args.now)
        if parsed is None:
            fail(f"--now does not parse: {args.now}")
        effective_until = parsed
    else:
        effective_until = now_kst()

    if effective_until < effective_since:
        fail(f"effective_until ({fmt(effective_until)}) is before "
             f"effective_since ({fmt(effective_since)})")

    span_delta = effective_until - effective_since
    span_seconds = span_delta.total_seconds()
    span_days = span_seconds / 86400

    label, step = pick_window_size(span_days, span_seconds)
    windows = build_windows(effective_since, effective_until, step)

    emit({
        "project": proj.name,
        "when_created": fmt(when_created),
        "effective_floor": fmt(effective_floor),
        "effective_since": fmt(effective_since),
        "effective_until": fmt(effective_until),
        "total_span_days": round(span_days, 2),
        "window_size": label,
        "total_windows": len(windows),
        "windows": windows,
        "as_of": now_kst_str(),
    })


if __name__ == "__main__":
    main()
