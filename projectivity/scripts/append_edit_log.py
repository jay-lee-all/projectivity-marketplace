#!/usr/bin/env python3
"""append_edit_log.py — write one entry to core/edits.jsonl.

Lazy-creates the file with the `_schema` line on first call. Allocates the
next sequential `edit-NNN` id by scanning existing entries. Atomic write.

Usage:
    append_edit_log.py --project <slug> \\
        --actor "Jay Lee" \\
        --target-file "projects/jobis/core/decisions.jsonl" \\
        --target-id "dec-042" \\
        --field "from" \\
        --before-json '"https://allganize.slack.com/..."' \\
        --after-json '"[[meetings/2026-03-12-jobis-kickoff]]"' \\
        [--reason "Backfilled meeting MD"]

Output (stdout, JSON):
    {"id": "edit-001", "logged": true, "path": "<abs>"}

Notes:
    - `before-json` / `after-json` accept any valid JSON value (string, array,
      object, etc.). Pass `null` literally if the field was previously absent.
    - `--reason` is required for the edits listed in conventions/edit-discipline.md
      ("Reason-required edits"). The skill enforces that policy; this script
      logs whatever it's given.
    - Schema: edits-v1, defined in conventions/edit-discipline.md.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import atomic_write, emit, fail, iter_jsonl, now_kst_str, project_root  # noqa: E402


SCHEMA_LINE = '{"_schema": "edits-v1"}\n'


def next_edit_id(path: Path) -> str:
    if not path.exists():
        return "edit-001"
    max_n = -1
    for obj in iter_jsonl(path):
        ident = obj.get("id")
        if not isinstance(ident, str) or not ident.startswith("edit-"):
            continue
        try:
            n = int(ident.split("-", 1)[1])
        except (ValueError, IndexError):
            continue
        if n > max_n:
            max_n = n
    nxt = max_n + 1 if max_n >= 0 else 1
    return f"edit-{nxt:03d}" if nxt < 1000 else f"edit-{nxt:04d}"


def parse_json_arg(name: str, raw: str):
    try:
        return json.loads(raw)
    except json.JSONDecodeError as e:
        fail(f"--{name} is not valid JSON: {e}")


def main() -> None:
    ap = argparse.ArgumentParser(description="Append one entry to core/edits.jsonl.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    ap.add_argument("--actor", required=True, help="PM running the edit (must match team.yaml)")
    ap.add_argument("--target-file", required=True, help="Vault-relative path of the file mutated")
    ap.add_argument("--target-id", required=True, help="Entry id touched (dec-NNN, ms-NNN, name, etc.)")
    ap.add_argument("--field", required=True, help="Field name on the entry")
    ap.add_argument("--before-json", required=True, help="Old value as a JSON literal")
    ap.add_argument("--after-json", required=True, help="New value as a JSON literal")
    ap.add_argument("--reason", help="Required for some edits per edit-discipline.md")
    args = ap.parse_args()

    proj = project_root(args.project, args.path)
    edits_path = proj / "core" / "edits.jsonl"

    before = parse_json_arg("before-json", args.before_json)
    after = parse_json_arg("after-json", args.after_json)

    entry = {
        "id": next_edit_id(edits_path),
        "when": now_kst_str(),
        "who": args.actor,
        "target_file": args.target_file,
        "target_id": args.target_id,
        "field": args.field,
        "before": before,
        "after": after,
    }
    if args.reason:
        entry["reason"] = args.reason

    line = json.dumps(entry, ensure_ascii=False) + "\n"

    if edits_path.exists():
        with edits_path.open("r", encoding="utf-8") as fh:
            existing = fh.read()
        new_content = existing + (line if existing.endswith("\n") or not existing else "\n" + line)
    else:
        edits_path.parent.mkdir(parents=True, exist_ok=True)
        new_content = SCHEMA_LINE + line

    atomic_write(edits_path, new_content)

    emit({"id": entry["id"], "logged": True, "path": str(edits_path)})


if __name__ == "__main__":
    main()
