#!/usr/bin/env python3
"""reconcile_cross_refs.py — one-pass orphan detection across a project.

Enumerates every defined bracket ID in JSONL + MD frontmatter, scans every
reference field (from/links/retires + narrative bracket tokens + MD body),
and returns:
  - defined_ids: which IDs exist (with source + type)
  - references: every reference with source, field, target
  - orphans: references whose target is not defined
  - defined_but_unreferenced: defined IDs with zero incoming references
    (informational — not every ID must be referenced)

Replaces the audit step 4 pattern of looping `link_graph.py` per ID.
`link_graph.py` stays the right tool for deep single-ID provenance tracing.

Usage:
    reconcile_cross_refs.py --project <slug>
    reconcile_cross_refs.py --path /abs/path/to/projects/<slug>

Output (stdout, JSON).
"""
from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

# Make sibling modules importable regardless of how the script was invoked.
sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import emit, iter_jsonl, load_frontmatter, project_root  # noqa: E402


# Full bracket ID (prefix + number) — BRACKET_ID_RE in _common.py captures only the prefix.
FULL_BRACKET_RE = re.compile(r"\[((?:dec|act|req|meet|risk)-\d{3,5})\]")
# Cross-project references are out of scope for single-project reconciliation.
CROSSPROJ_PREFIX_RE = re.compile(r"\[prj-\d{3}:")

JSONL_NARRATIVE_FIELDS = ("decision", "question", "context", "what", "reason")


def collect_defined_ids(proj: Path) -> dict[str, dict]:
    """Return {id: {"source": rel_path, "type": ...}} for every defined bracket ID."""
    defined: dict[str, dict] = {}

    for name in ("decisions.jsonl", "actions.jsonl"):
        p = proj / "core" / name
        rel = str(p.relative_to(proj))
        for entry in iter_jsonl(p):
            ident = entry.get("id")
            if isinstance(ident, str):
                defined[ident] = {"source": rel, "type": entry.get("type")}

    for sub in ("meetings", "requirements", "risks"):
        d = proj / sub
        if not d.is_dir():
            continue
        for md in sorted(d.glob("*.md")):
            meta, _ = load_frontmatter(md)
            ident = meta.get("id")
            if isinstance(ident, str):
                defined[ident] = {
                    "source": str(md.relative_to(proj)),
                    "type": meta.get("type") or sub.rstrip("s"),
                }
    return defined


def extract_bracket_refs(text: str) -> list[str]:
    """Return bracket IDs in text, skipping cross-project refs."""
    if not isinstance(text, str) or not text:
        return []
    # Strip out cross-project refs first so they don't match the inner id.
    text = CROSSPROJ_PREFIX_RE.sub("[PRJ_SCOPED:", text)
    return FULL_BRACKET_RE.findall(text)


def collect_references(proj: Path) -> list[dict]:
    """Return list of reference records: source_id, source_path, field, target."""
    refs: list[dict] = []

    # JSONL: structured fields + narrative fields.
    for name in ("decisions.jsonl", "actions.jsonl"):
        p = proj / "core" / name
        if not p.exists():
            continue
        rel = str(p.relative_to(proj))
        for entry in iter_jsonl(p):
            ident = entry.get("id")
            if not isinstance(ident, str):
                continue

            # `from`: string containing at most one bracket ID (or a wikilink; skip wikilinks).
            frm = entry.get("from")
            if isinstance(frm, str):
                for tgt in extract_bracket_refs(frm):
                    refs.append({"source_id": ident, "source_path": rel,
                                 "field": "from", "target": tgt})

            # `links` / `retires`: list of strings, each a bracket ID or bare token.
            for field in ("links", "retires"):
                v = entry.get(field)
                if isinstance(v, list):
                    for item in v:
                        if isinstance(item, str):
                            for tgt in extract_bracket_refs(item):
                                refs.append({"source_id": ident, "source_path": rel,
                                             "field": field, "target": tgt})

            # Narrative fields.
            for field in JSONL_NARRATIVE_FIELDS:
                v = entry.get(field)
                if isinstance(v, str):
                    for tgt in extract_bracket_refs(v):
                        refs.append({"source_id": ident, "source_path": rel,
                                     "field": field, "target": tgt})

    # MD bodies.
    for sub in ("meetings", "requirements", "risks"):
        d = proj / sub
        if not d.is_dir():
            continue
        for md in sorted(d.glob("*.md")):
            meta, body = load_frontmatter(md)
            ident = meta.get("id")
            rel = str(md.relative_to(proj))
            for tgt in extract_bracket_refs(body or ""):
                refs.append({"source_id": ident if isinstance(ident, str) else None,
                             "source_path": rel,
                             "field": "body",
                             "target": tgt})
    return refs


def main() -> None:
    ap = argparse.ArgumentParser(description="Project-wide bracket-ID reconciliation.")
    ap.add_argument("--project", required=False)
    ap.add_argument("--path", help="Explicit project path")
    args = ap.parse_args()

    proj = project_root(args.project, args.path)

    defined = collect_defined_ids(proj)
    references = collect_references(proj)

    defined_set = set(defined.keys())
    incoming: dict[str, list[dict]] = {ident: [] for ident in defined_set}
    orphans_map: dict[str, list[dict]] = {}

    for ref in references:
        target = ref["target"]
        locator = {"source_id": ref["source_id"],
                   "source_path": ref["source_path"],
                   "field": ref["field"]}
        if target in defined_set:
            incoming[target].append(locator)
        else:
            orphans_map.setdefault(target, []).append(locator)

    orphans = [{"target": t, "referenced_by": refs_list}
               for t, refs_list in sorted(orphans_map.items())]

    defined_but_unreferenced = sorted(
        ident for ident, inc in incoming.items() if not inc
    )

    emit({
        "project": proj.name,
        "defined_ids": defined,
        "references": references,
        "orphans": orphans,
        "defined_but_unreferenced": defined_but_unreferenced,
        "counts": {
            "defined": len(defined),
            "references": len(references),
            "orphans": len(orphans),
            "unreferenced": len(defined_but_unreferenced),
        },
    })


if __name__ == "__main__":
    main()
