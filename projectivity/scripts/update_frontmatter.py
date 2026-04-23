#!/usr/bin/env python3
"""update_frontmatter.py — set MD frontmatter fields, preserve body.

For meetings/, requirements/, risks/ MD files. Body is preserved verbatim.
Whitelist enforcement (which fields are immutable per kind) lives in
conventions/edit-discipline.md and is applied by the edit skill before
calling this script — but a few hard rules are enforced here as a defense
in depth.

Usage:
    update_frontmatter.py --file <path> \\
        --set status=done \\
        --set when_completed=2026-04-15T14:00:00 \\
        [--append-body "## Updates\\n\\n2026-04-15 — marked done [edit-007]"]

Output (stdout, JSON):
    {"updated": true, "file": "<abs>",
     "before": {<field>: <old>, ...},
     "after":  {<field>: <new>, ...}}

Notes:
    - Atomic write: temp file + fsync + rename.
    - --set may repeat; values are parsed as YAML scalars (so "true" → bool,
      "2026-04-15" stays a string unless YAML reads it otherwise).
    - --json-set takes a JSON-typed value: --json-set links='["[dec-001]"]'.
    - Hard-rejects edits to `id` and any `*_created` / `*_surfaced` field
      (these anchor entry identity per edit-discipline.md).
    - --append-body adds a literal block to the end of the body, separated
      by a blank line. Used by the edit skill to append `## Updates` /
      `## Resolution` lines as part of cascades.
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
    import frontmatter
except ImportError:  # pragma: no cover
    frontmatter = None  # type: ignore[assignment]

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


HARD_REJECT_FIELDS = {"id", "when_created", "when_surfaced"}
# Meeting `when` is also identity-anchoring (date-keyed). Reject it here too.
HARD_REJECT_FIELDS_MEETINGS = {"id", "when", "when_created", "when_surfaced"}


def parse_set(spec: str) -> tuple[str, Any]:
    if "=" not in spec:
        fail(f"--set expects key=value, got: {spec}")
    key, value = spec.split("=", 1)
    key = key.strip()
    # YAML scalar parse: handles bool/int/null/string. Bare strings stay strings.
    parsed = yaml.safe_load(value)
    return key, parsed


def parse_json_set(spec: str) -> tuple[str, Any]:
    if "=" not in spec:
        fail(f"--json-set expects key=json-value, got: {spec}")
    key, raw = spec.split("=", 1)
    try:
        return key.strip(), json.loads(raw)
    except json.JSONDecodeError as e:
        fail(f"--json-set {key}: invalid JSON value: {e}")


def main() -> None:
    if frontmatter is None:
        fail("python-frontmatter is required (pip install python-frontmatter)")
    if yaml is None:
        fail("PyYAML is required (pip install pyyaml)")

    ap = argparse.ArgumentParser(description="Set MD frontmatter fields, preserve body.")
    ap.add_argument("--file", required=True, help="Path to the MD file")
    ap.add_argument("--set", action="append", default=[],
                    help="key=value, repeatable (YAML scalar parse)")
    ap.add_argument("--json-set", action="append", default=[],
                    help="key=json-value, repeatable (for arrays/objects/etc.)")
    ap.add_argument("--append-body", help="Literal markdown to append to the end of the body")
    args = ap.parse_args()

    if not args.set and not args.json_set and not args.append_body:
        fail("nothing to do — pass --set, --json-set, or --append-body")

    path = Path(args.file).expanduser().resolve()
    if not path.exists():
        fail(f"file not found: {path}")

    is_meeting = "/meetings/" in str(path) or path.parent.name == "meetings"
    rejected = HARD_REJECT_FIELDS_MEETINGS if is_meeting else HARD_REJECT_FIELDS

    post = frontmatter.load(path)
    metadata: dict = dict(post.metadata)
    body: str = post.content

    before: dict = {}
    after: dict = {}

    updates: list[tuple[str, Any]] = []
    for spec in args.set:
        updates.append(parse_set(spec))
    for spec in args.json_set:
        updates.append(parse_json_set(spec))

    for key, value in updates:
        if key in rejected:
            fail(f"field `{key}` is hard-rejected on this entry type "
                 "(see conventions/edit-discipline.md)")
        before[key] = metadata.get(key)
        metadata[key] = value
        after[key] = value

    if args.append_body:
        appended = args.append_body
        body = body.rstrip() + "\n\n" + appended.rstrip() + "\n"

    new_post = frontmatter.Post(content=body, **metadata)
    rendered = frontmatter.dumps(new_post) + ("\n" if not body.endswith("\n") else "")

    atomic_write(path, rendered)

    emit({
        "updated": True,
        "file": str(path),
        "before": before,
        "after": after,
        "appended_body": bool(args.append_body),
    })


if __name__ == "__main__":
    main()
