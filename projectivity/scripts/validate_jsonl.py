#!/usr/bin/env python3
"""validate_jsonl.py — schema validator for decisions.jsonl / actions.jsonl.

Usage:
    validate_jsonl.py <path>
    validate_jsonl.py --stdin --kind decisions
    validate_jsonl.py --line '{"id":"dec-001",...}' --kind decisions

Exit codes:
    0 — valid
    2 — invalid (machine-readable details on stderr; human summary on stdout)

Notes:
    - Designed to be used by an `audit` skill and (later) a `PreToolUse` hook
      against `*.jsonl` writes.
    - Validates: required fields per type, ID shape, KST timestamp, type enum,
      reference field shapes, and the structural rules from `conventions/jsonl.md`
      (e.g. `decision-dropped` requires `from`; `retires` is `decision-made` →
      `decision-made` only; never targets MD entities).
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, iter_jsonl  # noqa: E402


ID_RE = re.compile(r"^(dec|act)-\d{3,5}$")
KST_TS_RE = re.compile(
    r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}\+09:00$"
)
BRACKET_ANY_RE = re.compile(r"^\[(dec|act|req|meet|risk)-\d{3,5}\]$")
BRACKET_DEC_RE = re.compile(r"^\[dec-\d{3,5}\]$")
BRACKET_ACT_RE = re.compile(r"^\[act-\d{3,5}\]$")
BRACKET_MD_RE = re.compile(r"^\[(req|meet|risk)-\d{3,5}\]$")
WIKILINK_RE = re.compile(r"^\[\[[^\]]+\]\]$")
CROSSPROJ_RE = re.compile(r"^\[prj-\d{3}:(dec|act|req|meet|risk)-\d{3,5}\]$")

DECISION_TYPES = {"decision-raised", "decision-made", "decision-dropped"}
ACTION_TYPES = {
    "task-created", "task-done", "task-blocked",
    "communication", "milestone", "milestone-shifted", "note",
}


def is_ref(s: str) -> bool:
    return bool(
        BRACKET_ANY_RE.match(s)
        or WIKILINK_RE.match(s)
        or CROSSPROJ_RE.match(s)
    )


def is_linear_token(s: str) -> bool:
    # Bare tokens: PREFIX-NNN. We don't have team.yaml here for prefix
    # validation; shape-only check.
    return bool(re.match(r"^[A-Z]{2,5}-\d{3,5}$", s))


def validate_decision(entry: dict, line_no: int, errors: list[str]) -> None:
    eid = entry.get("id", "?")
    typ = entry.get("type")

    # required: id, when, type
    for fld in ("id", "when", "type"):
        if not entry.get(fld):
            errors.append(f"line {line_no} ({eid}): missing required field `{fld}`")

    if entry.get("id") and not ID_RE.match(str(entry["id"])):
        errors.append(f"line {line_no} ({eid}): id does not match dec-NNN shape")
    if entry.get("when") and not KST_TS_RE.match(str(entry["when"])):
        errors.append(f"line {line_no} ({eid}): when must be ISO 8601 +09:00")
    if typ and typ not in DECISION_TYPES:
        errors.append(f"line {line_no} ({eid}): unknown type `{typ}`")

    # type-specific shape
    if typ == "decision-raised":
        if not entry.get("question"):
            errors.append(f"line {line_no} ({eid}): decision-raised needs `question`")
        if entry.get("decision"):
            errors.append(f"line {line_no} ({eid}): decision-raised must not have `decision` (use `question`)")
        if "retires" in entry:
            errors.append(f"line {line_no} ({eid}): decision-raised must not have `retires`")
    elif typ == "decision-made":
        if not entry.get("decision"):
            errors.append(f"line {line_no} ({eid}): decision-made needs `decision`")
        retires = entry.get("retires")
        if retires is not None:
            if not isinstance(retires, list):
                errors.append(f"line {line_no} ({eid}): retires must be an array")
            else:
                for r in retires:
                    if not isinstance(r, str) or not BRACKET_DEC_RE.match(r):
                        errors.append(
                            f"line {line_no} ({eid}): retires entry `{r}` must be [dec-NNN]; "
                            f"decision-made retires only target other decision-made"
                        )
                    if isinstance(r, str) and BRACKET_MD_RE.match(r):
                        errors.append(
                            f"line {line_no} ({eid}): retires must never target MD entities ({r}); "
                            f"MD entities retire via frontmatter"
                        )
    elif typ == "decision-dropped":
        if not entry.get("from"):
            errors.append(f"line {line_no} ({eid}): decision-dropped requires `from` pointing to the [dec-NNN] raised entry")
        else:
            if not BRACKET_DEC_RE.match(str(entry["from"])):
                errors.append(f"line {line_no} ({eid}): decision-dropped from must be [dec-NNN]")
        if "retires" in entry:
            errors.append(f"line {line_no} ({eid}): decision-dropped must not have `retires`")

    _validate_common_refs(entry, line_no, eid, errors)


def validate_action(entry: dict, line_no: int, errors: list[str]) -> None:
    eid = entry.get("id", "?")
    typ = entry.get("type")

    for fld in ("id", "when", "type"):
        if not entry.get(fld):
            errors.append(f"line {line_no} ({eid}): missing required field `{fld}`")

    if entry.get("id") and not ID_RE.match(str(entry["id"])):
        errors.append(f"line {line_no} ({eid}): id does not match act-NNN shape")
    if entry.get("when") and not KST_TS_RE.match(str(entry["when"])):
        errors.append(f"line {line_no} ({eid}): when must be ISO 8601 +09:00")
    if typ and typ not in ACTION_TYPES:
        errors.append(f"line {line_no} ({eid}): unknown type `{typ}`")

    if typ in {"task-created", "communication", "milestone", "milestone-shifted", "note"}:
        if not entry.get("what"):
            errors.append(f"line {line_no} ({eid}): {typ} needs `what`")
    if typ in {"task-done", "task-blocked"}:
        frm = entry.get("from")
        if not frm or not BRACKET_ACT_RE.match(str(frm)):
            errors.append(f"line {line_no} ({eid}): {typ} requires `from` pointing to [act-NNN]")

    retires = entry.get("retires")
    if retires is not None:
        if not isinstance(retires, list):
            errors.append(f"line {line_no} ({eid}): retires must be an array")
        else:
            for r in retires:
                if not isinstance(r, str) or not BRACKET_ACT_RE.match(r):
                    errors.append(
                        f"line {line_no} ({eid}): actions.retires must contain [act-NNN] only, got `{r}`"
                    )
                if isinstance(r, str) and BRACKET_MD_RE.match(r):
                    errors.append(
                        f"line {line_no} ({eid}): retires must never target MD entities ({r})"
                    )

    _validate_common_refs(entry, line_no, eid, errors)


def _validate_common_refs(entry: dict, line_no: int, eid: str, errors: list[str]) -> None:
    frm = entry.get("from")
    if frm is not None:
        if not isinstance(frm, str):
            errors.append(f"line {line_no} ({eid}): from must be a string")
        elif not is_ref(frm):
            errors.append(f"line {line_no} ({eid}): from has malformed reference `{frm}`")

    links = entry.get("links")
    if links is not None:
        if not isinstance(links, list):
            errors.append(f"line {line_no} ({eid}): links must be an array")
        else:
            for x in links:
                if not isinstance(x, str):
                    errors.append(f"line {line_no} ({eid}): links must contain strings")
                    continue
                if is_ref(x) or is_linear_token(x):
                    continue
                errors.append(
                    f"line {line_no} ({eid}): links entry `{x}` is neither a wikilink, "
                    f"a [prefix-NNN] bracket, nor a Linear-shape token"
                )


def detect_kind(path: Path) -> str | None:
    if path.name == "decisions.jsonl":
        return "decisions"
    if path.name == "actions.jsonl":
        return "actions"
    return None


def validate_lines(lines, kind: str) -> list[str]:
    errors: list[str] = []
    for i, raw in enumerate(lines, start=1):
        raw = raw.strip()
        if not raw:
            continue
        try:
            entry = json.loads(raw)
        except json.JSONDecodeError as e:
            errors.append(f"line {i}: invalid JSON — {e}")
            continue
        if isinstance(entry, dict) and "_schema" in entry:
            continue
        if kind == "decisions":
            validate_decision(entry, i, errors)
        else:
            validate_action(entry, i, errors)
    return errors


def main() -> None:
    ap = argparse.ArgumentParser(description="Validate decisions/actions JSONL.")
    ap.add_argument("path", nargs="?")
    ap.add_argument("--stdin", action="store_true")
    ap.add_argument("--line", help="Validate a single JSONL line")
    ap.add_argument("--kind", choices=("decisions", "actions"))
    args = ap.parse_args()

    if args.line:
        kind = args.kind
        if not kind:
            sys.stderr.write("--kind required with --line\n")
            sys.exit(2)
        errors = validate_lines([args.line], kind)
    elif args.stdin:
        kind = args.kind
        if not kind:
            sys.stderr.write("--kind required with --stdin\n")
            sys.exit(2)
        errors = validate_lines(sys.stdin.readlines(), kind)
    elif args.path:
        path = Path(args.path)
        if not path.exists():
            sys.stderr.write(f"file not found: {path}\n")
            sys.exit(2)
        kind = args.kind or detect_kind(path)
        if not kind:
            sys.stderr.write(f"cannot detect kind from filename {path.name}; pass --kind\n")
            sys.exit(2)
        with path.open("r", encoding="utf-8") as fh:
            errors = validate_lines(fh.readlines(), kind)
    else:
        ap.print_help()
        sys.exit(2)

    if errors:
        for e in errors:
            sys.stderr.write(e + "\n")
        emit({"valid": False, "error_count": len(errors)})
        sys.exit(2)
    emit({"valid": True})


if __name__ == "__main__":
    main()
