#!/usr/bin/env python3
"""link_graph.py — what points to / from a given bracket ID.

Builds a 1-hop link graph centered on an entry. Scans JSONL `from`/`links`/
`retires` and MD body wikilinks + bracket references.

Usage:
    link_graph.py <bracket-id> --project <slug>
    e.g. link_graph.py dec-007 --project woori

Output (stdout, JSON): {"target": ..., "incoming": [...], "outgoing": [...]}
    incoming = entries that reference target
    outgoing = entries target references
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import (  # noqa: E402
    BRACKET_ID_RE,
    WIKILINK_RE,
    emit,
    fail,
    iter_jsonl,
    load_frontmatter,
    project_root,
)


def normalize_id(s: str) -> str:
    return s.strip().strip("[]")


def md_files(proj: Path):
    for sub in ("meetings", "requirements", "risks"):
        d = proj / sub
        if d.is_dir():
            for md in d.glob("*.md"):
                yield md


def jsonl_files(proj: Path):
    for name in ("decisions.jsonl", "actions.jsonl"):
        p = proj / "core" / name
        if p.exists():
            yield p


def collect_outgoing_jsonl(entry: dict) -> list[str]:
    refs: list[str] = []
    frm = entry.get("from")
    if isinstance(frm, str):
        refs.append(frm)
    for k in ("links", "retires"):
        v = entry.get(k)
        if isinstance(v, list):
            refs.extend(x for x in v if isinstance(x, str))
    # also free-text bracket IDs in narrative fields
    for fld in ("decision", "question", "context", "what"):
        v = entry.get(fld)
        if isinstance(v, str):
            refs.extend(BRACKET_ID_RE.findall(v))  # returns prefix only :-(
    return refs


def main() -> None:
    ap = argparse.ArgumentParser(description="1-hop link graph for a bracket ID.")
    ap.add_argument("bracket_id", help="e.g. dec-007 or [dec-007]")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    args = ap.parse_args()

    target = normalize_id(args.bracket_id)
    if not re.match(r"^(dec|act|req|meet|risk)-\d{3,5}$", target):
        fail(f"not a recognized bracket id: {args.bracket_id}")

    proj = project_root(args.project, args.path)

    incoming: list[dict] = []
    outgoing: list[dict] = []

    # JSONL: scan every entry; check membership both directions.
    for jpath in jsonl_files(proj):
        for entry in iter_jsonl(jpath):
            ident = entry.get("id")
            if not isinstance(ident, str):
                continue
            text_blob = ""
            for fld in ("decision", "question", "context", "what"):
                v = entry.get(fld)
                if isinstance(v, str):
                    text_blob += " " + v
            link_blob = []
            frm = entry.get("from")
            if isinstance(frm, str):
                link_blob.append(frm)
            for k in ("links", "retires"):
                v = entry.get(k)
                if isinstance(v, list):
                    link_blob.extend(x for x in v if isinstance(x, str))
            link_blob_str = " ".join(link_blob)

            if ident == target:
                # outgoing from target
                bracket_refs = set(BRACKET_ID_RE.findall(text_blob + " " + link_blob_str))
                # The regex captures only the prefix; re-extract full IDs:
                full_refs = set(re.findall(r"\[((?:dec|act|req|meet|risk)-\d{3,5})\]",
                                            text_blob + " " + link_blob_str))
                wikilinks = set(WIKILINK_RE.findall(text_blob + " " + link_blob_str))
                outgoing.append({
                    "source": "self",
                    "from_field": frm,
                    "links": entry.get("links"),
                    "retires": entry.get("retires"),
                    "bracket_refs_in_text": sorted(full_refs),
                    "wikilinks_in_text": sorted(wikilinks),
                })
                continue

            # incoming: does any field reference target?
            if f"[{target}]" in (text_blob + " " + link_blob_str):
                incoming.append({
                    "source": str(jpath.name),
                    "id": ident,
                    "type": entry.get("type"),
                    "via": _which_field(entry, target),
                })

    # MD files: scan body for [target] or wikilinks targeting frontmatter.id == target.
    for md in md_files(proj):
        meta, body = load_frontmatter(md)
        ident = meta.get("id")
        rel = str(md.relative_to(proj))
        if ident == target:
            full_refs = set(re.findall(r"\[((?:dec|act|req|meet|risk)-\d{3,5})\]", body))
            wikilinks = set(WIKILINK_RE.findall(body))
            outgoing.append({
                "source": rel,
                "bracket_refs_in_body": sorted(full_refs),
                "wikilinks_in_body": sorted(wikilinks),
            })
        elif f"[{target}]" in body:
            incoming.append({
                "source": rel,
                "id": ident,
                "type": meta.get("type"),
                "via": "body",
            })

    emit({
        "project": proj.name,
        "target": target,
        "incoming": incoming,
        "outgoing": outgoing,
    })


def _which_field(entry: dict, target: str) -> str:
    needle = f"[{target}]"
    if needle in str(entry.get("from") or ""):
        return "from"
    for k in ("links", "retires"):
        v = entry.get(k)
        if isinstance(v, list) and any(needle == s for s in v if isinstance(s, str)):
            return k
    for fld in ("decision", "question", "context", "what"):
        v = entry.get(fld)
        if isinstance(v, str) and needle in v:
            return fld
    return "?"


if __name__ == "__main__":
    main()
