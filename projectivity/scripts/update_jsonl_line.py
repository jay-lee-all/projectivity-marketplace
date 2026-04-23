#!/usr/bin/env python3
"""update_jsonl_line.py — replace one entry in a JSONL file by id.

Atomic write. The line being replaced must already exist (no inserts; use
curate to append new entries). Other lines are preserved byte-for-byte
except for trailing-newline normalization.

Usage:
    update_jsonl_line.py --file <path> --id <id> --json '<new-line-json>' \\
        [--kind decisions|actions]

Output (stdout, JSON):
    {"updated": true, "id": "dec-042", "path": "<abs>",
     "before": <old-entry>, "after": <new-entry>}

Notes:
    - The new line is pre-validated via validate_jsonl.py's machinery if
      --kind is supplied or auto-detected from the filename. Validation
      failure exits 2 without touching the file.
    - The new entry's `id` must match the `--id` argument — id changes are
      a hard reject (id is identity per edit-discipline.md).
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import atomic_write, emit, fail  # noqa: E402
from validate_jsonl import detect_kind, validate_lines  # noqa: E402


def main() -> None:
    ap = argparse.ArgumentParser(description="Replace one JSONL entry by id (atomic).")
    ap.add_argument("--file", required=True, help="Path to decisions.jsonl / actions.jsonl")
    ap.add_argument("--id", required=True, help="Entry id to replace (e.g. dec-042)")
    ap.add_argument("--json", required=True, help="Replacement entry as a single JSON object")
    ap.add_argument("--kind", choices=("decisions", "actions"),
                    help="Override schema detection (otherwise inferred from filename)")
    args = ap.parse_args()

    path = Path(args.file).expanduser().resolve()
    if not path.exists():
        fail(f"file not found: {path}")

    try:
        new_entry = json.loads(args.json)
    except json.JSONDecodeError as e:
        fail(f"--json is not valid JSON: {e}")

    if not isinstance(new_entry, dict):
        fail("--json must be a JSON object")

    if new_entry.get("id") != args.id:
        fail(f"--json `id` ({new_entry.get('id')!r}) does not match --id ({args.id!r}); "
             "id changes are not permitted")

    kind = args.kind or detect_kind(path)
    if not kind:
        fail(f"cannot detect kind from filename {path.name}; pass --kind")

    # Pre-validate the new line. Errors exit 2.
    errors, _warnings = validate_lines([args.json], kind)
    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        emit({"updated": False, "error_count": len(errors)})
        sys.exit(2)

    # Read all lines, find the target by id, replace.
    with path.open("r", encoding="utf-8") as fh:
        raw_lines = fh.readlines()

    new_lines: list[str] = []
    before_entry = None
    replaced = False
    for raw in raw_lines:
        stripped = raw.strip()
        if not stripped:
            new_lines.append(raw)
            continue
        try:
            obj = json.loads(stripped)
        except json.JSONDecodeError:
            new_lines.append(raw)
            continue
        if isinstance(obj, dict) and obj.get("id") == args.id:
            if replaced:
                fail(f"duplicate id {args.id!r} in {path} — refusing to update an ambiguous file")
            before_entry = obj
            new_lines.append(json.dumps(new_entry, ensure_ascii=False) + "\n")
            replaced = True
        else:
            new_lines.append(raw if raw.endswith("\n") else raw + "\n")

    if not replaced:
        fail(f"id {args.id!r} not found in {path}")

    atomic_write(path, "".join(new_lines))

    emit({
        "updated": True,
        "id": args.id,
        "path": str(path),
        "before": before_entry,
        "after": new_entry,
    })


if __name__ == "__main__":
    main()
