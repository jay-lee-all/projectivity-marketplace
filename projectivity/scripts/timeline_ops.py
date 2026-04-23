#!/usr/bin/env python3
"""timeline_ops.py — structured operations on timeline.yaml.

The shape of timeline.yaml is four lists at the top level: `milestones`,
`done`, `dropped`, `deadlines`. Edit operations preserve that shape and
allocate new ms-NNN / dl-NNN ids by scanning all four buckets.

Operations (one per invocation):

    --add-milestone --when 2026-05-15 --title "GA cut" [--description "..."]
        Allocates next ms-NNN, appends to milestones:.

    --mark-done --id ms-003 --completed 2026-04-15
        Moves entry from milestones: to done:, sets completed.

    --shift --id ms-003 --to 2026-05-22
        Updates `when:` on the milestones: entry. Reason lives in the cascaded
        actions.jsonl write the skill issues separately — this script only
        touches timeline.yaml.

    --drop --id ms-003 --on 2026-04-20
        Moves entry from milestones: to dropped:, sets dropped_on.

    --add-deadline --date 2026-06-01 --what "Customer-facing GA"
        Allocates next dl-NNN, appends to deadlines:.

    --edit-deadline --id dl-002 --date 2026-06-05
        Updates `date:` on a deadlines: entry.

    --edit-milestone-field --id ms-003 --field title --value "New title"
        Edits a non-`when` field on a milestones: entry (title, description).

Output (stdout, JSON):
    {"updated": true, "file": "<abs>", "operation": "...",
     "id": "ms-003", "before": {...}, "after": {...}}

Notes:
    - Atomic write: temp file + fsync + rename.
    - Refuses id changes; ms-NNN and dl-NNN are stable per edit-discipline.md.
    - Reasons / cascade JSONL entries are the skill's responsibility, not
      this script's. This script only mutates timeline.yaml.
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path
from typing import Any

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import atomic_write, emit, fail  # noqa: E402

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


DATE_RE = re.compile(r"^\d{4}-\d{2}-\d{2}$")
MS_RE = re.compile(r"^ms-\d{3,5}$")
DL_RE = re.compile(r"^dl-\d{3,5}$")


def load(path: Path) -> tuple[dict, str]:
    if yaml is None:
        fail("PyYAML is required (pip install pyyaml)")
    if not path.exists():
        fail(f"file not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        text = fh.read()
    data = yaml.safe_load(text) or {}
    if not isinstance(data, dict):
        fail(f"{path}: top-level must be a mapping with milestones/done/dropped/deadlines lists")
    for key in ("milestones", "done", "dropped", "deadlines"):
        if key not in data or data[key] is None:
            data[key] = []
        if not isinstance(data[key], list):
            fail(f"{path}: `{key}:` must be a list")
    return data, text


def save(path: Path, data: dict, original_text: str) -> None:
    header_lines = []
    for line in original_text.splitlines(keepends=True):
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    header = "".join(header_lines)
    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)
    atomic_write(path, header + body if header else body)


def next_id(data: dict, prefix: str) -> str:
    """Scan every bucket for ids with the given prefix; return prefix + (max+1)."""
    max_n = -1
    for bucket in ("milestones", "done", "dropped", "deadlines"):
        for entry in data[bucket]:
            if not isinstance(entry, dict):
                continue
            ident = entry.get("id")
            if not isinstance(ident, str) or not ident.startswith(prefix):
                continue
            try:
                n = int(ident[len(prefix):])
            except ValueError:
                continue
            if n > max_n:
                max_n = n
    nxt = max_n + 1 if max_n >= 0 else 1
    return f"{prefix}{nxt:03d}" if nxt < 1000 else f"{prefix}{nxt:04d}"


def find_in(bucket: list[dict], ident: str) -> dict | None:
    for entry in bucket:
        if isinstance(entry, dict) and entry.get("id") == ident:
            return entry
    return None


def require_date(name: str, value: str) -> None:
    if not value or not DATE_RE.match(value):
        fail(f"--{name} must be YYYY-MM-DD, got: {value!r}")


def op_add_milestone(data: dict, args) -> tuple[dict, dict, str]:
    require_date("when", args.when)
    if not args.title:
        fail("--title is required for --add-milestone")
    new_id = next_id(data, "ms-")
    entry: dict = {"id": new_id, "when": args.when, "title": args.title}
    if args.description:
        entry["description"] = args.description
    data["milestones"].append(entry)
    return entry, entry, new_id


def op_mark_done(data: dict, args) -> tuple[dict, dict, str]:
    if not args.id or not MS_RE.match(args.id):
        fail("--id must be ms-NNN for --mark-done")
    require_date("completed", args.completed)
    entry = find_in(data["milestones"], args.id)
    if entry is None:
        fail(f"{args.id} not found in milestones: bucket")
    before = dict(entry)
    after = {"id": args.id, "completed": args.completed}
    data["milestones"].remove(entry)
    data["done"].append(after)
    return before, after, args.id


def op_shift(data: dict, args) -> tuple[dict, dict, str]:
    if not args.id or not MS_RE.match(args.id):
        fail("--id must be ms-NNN for --shift")
    require_date("to", args.to)
    entry = find_in(data["milestones"], args.id)
    if entry is None:
        fail(f"{args.id} not found in milestones: bucket")
    before = dict(entry)
    entry["when"] = args.to
    return before, dict(entry), args.id


def op_drop(data: dict, args) -> tuple[dict, dict, str]:
    if not args.id or not MS_RE.match(args.id):
        fail("--id must be ms-NNN for --drop")
    require_date("on", args.on)
    entry = find_in(data["milestones"], args.id)
    if entry is None:
        fail(f"{args.id} not found in milestones: bucket")
    before = dict(entry)
    after = {"id": args.id, "dropped_on": args.on}
    data["milestones"].remove(entry)
    data["dropped"].append(after)
    return before, after, args.id


def op_add_deadline(data: dict, args) -> tuple[dict, dict, str]:
    require_date("date", args.date)
    if not args.what:
        fail("--what is required for --add-deadline")
    new_id = next_id(data, "dl-")
    entry = {"id": new_id, "date": args.date, "what": args.what}
    data["deadlines"].append(entry)
    return entry, entry, new_id


def op_edit_deadline(data: dict, args) -> tuple[dict, dict, str]:
    if not args.id or not DL_RE.match(args.id):
        fail("--id must be dl-NNN for --edit-deadline")
    entry = find_in(data["deadlines"], args.id)
    if entry is None:
        fail(f"{args.id} not found in deadlines: bucket")
    before = dict(entry)
    if args.date is not None:
        require_date("date", args.date)
        entry["date"] = args.date
    if args.what is not None:
        entry["what"] = args.what
    if before == entry:
        fail("--edit-deadline requires --date and/or --what to actually change")
    return before, dict(entry), args.id


def op_edit_milestone_field(data: dict, args) -> tuple[dict, dict, str]:
    if not args.id or not MS_RE.match(args.id):
        fail("--id must be ms-NNN for --edit-milestone-field")
    if args.field not in {"title", "description", "when"}:
        fail(f"--field must be one of title/description/when, got: {args.field}")
    entry = find_in(data["milestones"], args.id)
    if entry is None:
        fail(f"{args.id} not found in milestones: bucket "
             "(this op edits open milestones only; use --shift / --mark-done / --drop for state changes)")
    if args.value is None:
        fail("--value is required for --edit-milestone-field")
    if args.field == "when":
        require_date("value", args.value)
    before = dict(entry)
    entry[args.field] = args.value
    return before, dict(entry), args.id


OPERATIONS = {
    "add-milestone": op_add_milestone,
    "mark-done": op_mark_done,
    "shift": op_shift,
    "drop": op_drop,
    "add-deadline": op_add_deadline,
    "edit-deadline": op_edit_deadline,
    "edit-milestone-field": op_edit_milestone_field,
}


def main() -> None:
    ap = argparse.ArgumentParser(description="Structured operations on timeline.yaml.")
    ap.add_argument("--file", required=True, help="Path to timeline.yaml")

    op_group = ap.add_mutually_exclusive_group(required=True)
    op_group.add_argument("--add-milestone", action="store_true")
    op_group.add_argument("--mark-done", action="store_true")
    op_group.add_argument("--shift", action="store_true")
    op_group.add_argument("--drop", action="store_true")
    op_group.add_argument("--add-deadline", action="store_true")
    op_group.add_argument("--edit-deadline", action="store_true")
    op_group.add_argument("--edit-milestone-field", action="store_true")

    ap.add_argument("--id", help="Existing ms-NNN or dl-NNN")
    ap.add_argument("--when", help="Date for --add-milestone (YYYY-MM-DD)")
    ap.add_argument("--title", help="Title for --add-milestone")
    ap.add_argument("--description", help="Optional description for --add-milestone")
    ap.add_argument("--completed", help="Date for --mark-done (YYYY-MM-DD)")
    ap.add_argument("--to", help="New date for --shift (YYYY-MM-DD)")
    ap.add_argument("--on", help="Date for --drop (YYYY-MM-DD)")
    ap.add_argument("--date", help="Date for --add-deadline / --edit-deadline (YYYY-MM-DD)")
    ap.add_argument("--what", help="Description for --add-deadline / --edit-deadline")
    ap.add_argument("--field", help="Field name for --edit-milestone-field")
    ap.add_argument("--value", help="Value for --edit-milestone-field")
    args = ap.parse_args()

    chosen = next(name for name in OPERATIONS if getattr(args, name.replace("-", "_")))

    path = Path(args.file).expanduser().resolve()
    data, original_text = load(path)

    before, after, target_id = OPERATIONS[chosen](data, args)
    save(path, data, original_text)

    emit({
        "updated": True,
        "file": str(path),
        "operation": chosen,
        "id": target_id,
        "before": before,
        "after": after,
    })


if __name__ == "__main__":
    main()
