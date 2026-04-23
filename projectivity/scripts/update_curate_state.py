#!/usr/bin/env python3
"""update_curate_state.py — update core/curate-state.yaml after a curate run.

Machine-maintained file; curate is the only writer after scaffold's initial
seed. This script is how curate writes. See conventions/curate-state.md for
the schema + contract.

Usage:
    update_curate_state.py --project <slug> --mode backfill|incremental \\
        [--source <name>=<ts>]... [--when <ts>]

    # Source names map to specific timestamp fields per conventions/curate-state.md:
    #   slack_internal  -> last_message_ts
    #   slack_external  -> last_message_ts
    #   linear          -> last_issue_updated_at
    #   email           -> last_thread_ts

    # Timestamps are naive ISO 8601 KST (e.g. 2026-04-23T18:30:00). No offset.

Example:
    update_curate_state.py --project jobis --mode incremental \\
        --source slack_internal=2026-04-23T14:30:00 \\
        --source linear=2026-04-23T12:00:00

Output (stdout, JSON): {"project": ..., "updated_sources": [...], "mode": ..., "when": ...}
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, fail, now_kst_str, parse_kst, project_root  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


# Source name -> timestamp field name. Authoritative per conventions/curate-state.md.
SOURCE_FIELD = {
    "slack_internal": "last_message_ts",
    "slack_external": "last_message_ts",
    "linear": "last_issue_updated_at",
    "email": "last_thread_ts",
}

HEADER = (
    "# Machine-maintained. Do not edit by hand.\n"
    "# Schema + contract: conventions/curate-state.md.\n"
    "# Read at the start of every curate run; updated after a successful write.\n"
    "\n"
)


def parse_source_updates(items: list[str]) -> list[tuple[str, str]]:
    out = []
    for item in items:
        if "=" not in item:
            fail(f"--source expects name=timestamp, got: {item}")
        name, ts = item.split("=", 1)
        name = name.strip()
        ts = ts.strip()
        if name not in SOURCE_FIELD:
            fail(f"unknown source name: {name} (known: {', '.join(sorted(SOURCE_FIELD))})")
        if parse_kst(ts) is None:
            fail(f"--source {name}: timestamp does not parse as naive ISO 8601 KST: {ts}")
        out.append((name, ts))
    return out


def main() -> None:
    if yaml is None:
        fail("PyYAML is required (pip install pyyaml)")

    ap = argparse.ArgumentParser(description="Update core/curate-state.yaml after a curate run.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    ap.add_argument("--mode", required=True, choices=["backfill", "incremental"])
    ap.add_argument("--source", action="append", default=[],
                    help="name=timestamp, repeatable. Names: "
                         + ", ".join(sorted(SOURCE_FIELD)))
    ap.add_argument("--when", default=None,
                    help="Completion time (default: now in naive KST)")
    args = ap.parse_args()

    proj = project_root(args.project, args.path)
    state_path = proj / "core" / "curate-state.yaml"
    if not state_path.exists():
        fail(f"curate-state.yaml not found: {state_path} (scaffold should have created it)")

    when = args.when or now_kst_str()
    if parse_kst(when) is None:
        fail(f"--when does not parse as naive ISO 8601 KST: {when}")

    updates = parse_source_updates(args.source)

    with state_path.open("r", encoding="utf-8") as fh:
        data = yaml.safe_load(fh) or {}

    sources = data.get("sources")
    if not isinstance(sources, dict):
        fail(f"{state_path}: 'sources' block is missing or malformed")

    updated_names: list[str] = []
    for name, ts in updates:
        block = sources.get(name)
        if not isinstance(block, dict):
            fail(f"source '{name}' is not present in {state_path}. "
                 f"Scaffold creates source blocks; this script only updates them.")
        field = SOURCE_FIELD[name]
        block[field] = ts
        updated_names.append(name)

    data["sources"] = sources
    data["last_run"] = {"mode": args.mode, "when": when}

    with state_path.open("w", encoding="utf-8") as fh:
        fh.write(HEADER)
        yaml.safe_dump(data, fh, sort_keys=False, allow_unicode=True, default_flow_style=False)

    emit({
        "project": proj.name,
        "updated_sources": updated_names,
        "mode": args.mode,
        "when": when,
        "path": str(state_path),
    })


if __name__ == "__main__":
    main()
