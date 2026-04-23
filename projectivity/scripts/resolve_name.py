#!/usr/bin/env python3
"""resolve_name.py — token → canonical person record.

Resolves a name, Slack ID, Slack handle, email, GitHub handle, or Linear
handle to the canonical entry from team.yaml + (optional) contacts.yaml.

Usage:
    resolve_name.py <token> [--team team.yaml] [--contacts contacts.yaml]
    resolve_name.py --tokens token1 token2 ... [--team team.yaml]

Output (stdout, JSON):
    {
      "matches": [
        {"input": "U093ZAFDNTB", "match": {"name": "Meera Hong", ...}, "via": "slack"}
      ],
      "unresolved": ["someone"]
    }

Notes:
    - Match is exact, case-insensitive on string fields.
    - Returns first match per token; ambiguities are reported as multiple
      records under "ambiguous" rather than guessing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, fail, load_yaml  # noqa: E402


LOOKUP_FIELDS = ("name", "korean_name", "email", "slack", "slack_name", "github", "linear")


def normalize(s) -> str:
    return str(s).strip().lower() if s is not None else ""


def build_index(records: list[dict]) -> dict[tuple[str, str], list[dict]]:
    """Map (field, normalized_value) → list of records."""
    idx: dict[tuple[str, str], list[dict]] = {}
    for rec in records:
        if not isinstance(rec, dict):
            continue
        for field in LOOKUP_FIELDS:
            v = rec.get(field)
            if not v:
                continue
            key = (field, normalize(v))
            idx.setdefault(key, []).append(rec)
    return idx


def resolve_one(token: str, idx) -> dict:
    norm = normalize(token)
    hits: list[tuple[str, dict]] = []
    seen_ids = set()
    for field in LOOKUP_FIELDS:
        for rec in idx.get((field, norm), []):
            rid = id(rec)
            if rid in seen_ids:
                continue
            seen_ids.add(rid)
            hits.append((field, rec))
    if not hits:
        return {"input": token, "match": None}
    if len(hits) == 1:
        field, rec = hits[0]
        return {"input": token, "via": field, "match": rec}
    return {
        "input": token,
        "ambiguous": [{"via": f, "match": r} for f, r in hits],
    }


def main() -> None:
    ap = argparse.ArgumentParser(description="Resolve a token to a team member.")
    ap.add_argument("token", nargs="?")
    ap.add_argument("--tokens", nargs="+", help="Resolve multiple tokens")
    ap.add_argument("--team", default="team.yaml")
    ap.add_argument("--contacts", default=None)
    args = ap.parse_args()

    tokens = args.tokens if args.tokens else ([args.token] if args.token else [])
    if not tokens:
        fail("provide a token (positional) or --tokens")

    team_path = Path(args.team)
    records: list[dict] = []
    team_data = load_yaml(team_path)
    if isinstance(team_data, list):
        records.extend(team_data)
    elif isinstance(team_data, dict) and "team" in team_data:
        records.extend(team_data.get("team") or [])
    else:
        fail(f"unexpected team.yaml shape: {type(team_data).__name__}")

    if args.contacts:
        contacts_path = Path(args.contacts)
        if contacts_path.exists():
            cdata = load_yaml(contacts_path)
            if isinstance(cdata, list):
                records.extend(cdata)
            elif isinstance(cdata, dict):
                # contacts.yaml may group by org/customer
                for v in cdata.values():
                    if isinstance(v, list):
                        records.extend(v)

    idx = build_index(records)
    matches = []
    unresolved = []
    for tok in tokens:
        result = resolve_one(tok, idx)
        if result.get("match") is None and "ambiguous" not in result:
            unresolved.append(tok)
        else:
            matches.append(result)

    emit({"matches": matches, "unresolved": unresolved})


if __name__ == "__main__":
    main()
