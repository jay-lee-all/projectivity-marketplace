#!/usr/bin/env python3
"""update_yaml_field.py — set one field on one record in a YAML file.

Designed for `team.yaml` and project `core/contacts.yaml`. Records are
identified by a `name` selector (the only stable key per edit-discipline.md;
`name` itself is reference-fragile and not editable here).

Usage:
    update_yaml_field.py --file <path> --select "name=Alice" \\
        --field role --value "Engineering Manager"

    # Set a value that is not a plain string (e.g. an array): pass --json-value
    update_yaml_field.py --file <path> --select "name=Alice" \\
        --field tags --json-value '["lead","backend"]'

Output (stdout, JSON):
    {"updated": true, "file": "<abs>", "select": "name=Alice",
     "field": "role", "before": "PM", "after": "Engineering Manager"}

Notes:
    - Atomic write: temp file + fsync + rename.
    - Refuses --field name (reference-fragile per edit-discipline.md).
    - File shape supported: top-level `team:` or `contacts:` key with a list
      of dicts, OR a top-level list of dicts. Other shapes are rejected.
"""
from __future__ import annotations

import argparse
import json
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


REFERENCE_FRAGILE_FIELDS = {"name"}


def parse_select(spec: str) -> tuple[str, str]:
    if "=" not in spec:
        fail(f"--select expects key=value, got: {spec}")
    key, value = spec.split("=", 1)
    return key.strip(), value.strip()


def find_records_list(data: Any, path: Path) -> list[dict]:
    """Locate the editable list of dict records in the loaded YAML."""
    if isinstance(data, list):
        return data
    if isinstance(data, dict):
        for key in ("team", "contacts"):
            if key in data and isinstance(data[key], list):
                return data[key]
        # Allow nested per-org structure: contacts: { customer-org: [ ... ] }.
        # Pick the first list-of-dicts found at depth 1 if "contacts" maps to a dict.
        if "contacts" in data and isinstance(data["contacts"], dict):
            for org_key, val in data["contacts"].items():
                if isinstance(val, list):
                    return val
    fail(f"{path}: cannot locate a top-level records list (expected `team:` or `contacts:` list, "
         "or a bare list at the document root)")


def main() -> None:
    if yaml is None:
        fail("PyYAML is required (pip install pyyaml)")

    ap = argparse.ArgumentParser(description="Set one field on one record in a YAML file.")
    ap.add_argument("--file", required=True, help="Path to team.yaml / contacts.yaml")
    ap.add_argument("--select", required=True, help="key=value to identify the record (e.g. name=Alice)")
    ap.add_argument("--field", required=True, help="Field to set on the matched record")
    ap.add_argument("--value", help="New value (string)")
    ap.add_argument("--json-value", help="New value as a JSON literal (for arrays/objects/numbers/null)")
    args = ap.parse_args()

    if (args.value is None) == (args.json_value is None):
        fail("provide exactly one of --value or --json-value")

    if args.field in REFERENCE_FRAGILE_FIELDS:
        fail(f"field `{args.field}` is reference-fragile and cannot be edited "
             "(see conventions/edit-discipline.md)")

    path = Path(args.file).expanduser().resolve()
    if not path.exists():
        fail(f"file not found: {path}")

    sel_key, sel_value = parse_select(args.select)

    if args.json_value is not None:
        try:
            new_value = json.loads(args.json_value)
        except json.JSONDecodeError as e:
            fail(f"--json-value is not valid JSON: {e}")
    else:
        new_value = args.value

    with path.open("r", encoding="utf-8") as fh:
        original_text = fh.read()
    data = yaml.safe_load(original_text) or {}

    records = find_records_list(data, path)

    matches = [r for r in records if isinstance(r, dict) and r.get(sel_key) == sel_value]
    if not matches:
        fail(f"no record in {path} matches {sel_key}={sel_value!r}")
    if len(matches) > 1:
        fail(f"{len(matches)} records match {sel_key}={sel_value!r} in {path} — selector is ambiguous")

    record = matches[0]
    before = record.get(args.field)
    record[args.field] = new_value

    # Preserve the leading comment header if the original file started with `#` lines.
    header_lines = []
    for line in original_text.splitlines(keepends=True):
        if line.startswith("#") or line.strip() == "":
            header_lines.append(line)
        else:
            break
    header = "".join(header_lines)

    body = yaml.safe_dump(data, sort_keys=False, allow_unicode=True, default_flow_style=False)

    atomic_write(path, header + body if header else body)

    emit({
        "updated": True,
        "file": str(path),
        "select": args.select,
        "field": args.field,
        "before": before,
        "after": new_value,
    })


if __name__ == "__main__":
    main()
