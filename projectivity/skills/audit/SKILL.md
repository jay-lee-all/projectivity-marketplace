---
description: Read-only integrity check across a project vault. Surfaces schema violations, orphan references, stale entries, broken wikilinks, thin MDs, and inconsistent names. Never auto-fixes — reports only. Use periodically (weekly or before a release) or after major curation work to catch drift before it compounds.
---

# audit — vault integrity check

## When to Use

Regular hygiene pass: weekly, after heavy curation, or before shipping a plugin release. Catches:

- Schema violations in JSONL (missing fields, wrong types, malformed references).
- Orphan bracket IDs (references to entries that don't exist).
- Stale `decision-raised` entries (aged past threshold with no `from`-closure).
- Risks open longer than their expected lifecycle.
- MDs with thin bodies relative to their frontmatter claims.
- Name inconsistencies (same person, different spellings across files).

Read-only by contract. The PM (or `curate`) acts on audit findings; the audit skill does not.

## Conventions Loaded at Skill Start

All of them. Audit needs the full rule set: `conventions/jsonl.md`, `conventions/references.md`, `conventions/timestamps.md`, `conventions/linear-tickets.md`, `conventions/md-meetings.md`, `conventions/md-requirements.md`, `conventions/md-risks.md`.

## Workflow

1. **Scope the audit.** Per-project by default. Cross-project audit is a distinct invocation — confirm which with the PM if ambiguous.

2. **JSONL schema check.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/actions.jsonl"
   ```

   Non-zero exit means structural violations. List them verbatim — don't paraphrase.

3. **Orphan references.** For every bracket ID referenced (`from`, `links`, `retires`, body wikilinks), confirm the target exists:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/link_graph.py" <some-id> --project <slug>
   ```

   Cross-check against the union of all defined IDs in JSONL + MD frontmatter.

4. **Stale raised decisions.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/aging_pending.py" --project <slug> --threshold 30
   ```

   Surface anything older than 30 days with no `from`-closure. This is stricter than `brief`'s 14-day nudge — audit catches the long-forgotten ones.

5. **Open risks past category-specific thresholds.** Infrastructure risks open > 14 days, customer risks open > 30 days, etc. Use `frontmatter_index.py` with `--filter when_resolved=` to pull open risks, then compare `when_surfaced` against thresholds.

6. **Name consistency.** Run `resolve_name.py` over every `who` field in JSONL + every `attendees` entry in meeting MDs. Flag tokens that fall into the `unresolved` bucket or that resolve via different fields across files (e.g. one entry uses the Slack ID, another uses the name).

7. **Thin MDs.** Requirements with `status: active` but an empty Spec section. Risks with no Investigation section and `when_surfaced` older than 7 days. Heuristic, not strict — call these out as "likely thin" and let the PM decide.

8. **Temporary-mitigation drift.** Risks with `category: configuration` that have no reversion/formalization conditions in the body. The convention requires these; audit enforces.

9. **Report.** One grouped findings document:

   ```
   ## Schema violations
   ## Orphan references
   ## Stale raised decisions
   ## Aging open risks
   ## Name inconsistencies
   ## Thin MDs
   ## Temporary-mitigation drift
   ```

   Each finding names the file/line/ID. The PM reads, triages, and acts — audit does not.

## Gotchas

- **No auto-fix, ever.** Auto-fixing on a curated vault is how silent drift happens. Surface, don't correct.
- **`check-resolvable` is plugin-maintainer scope.** Audit covers vault data, not plugin health (resolver/skill drift). Those are separate concerns.
- **False positives.** Thin-MD and stale-decision heuristics will catch legitimate cases (a decision-raised is legitimately paused waiting on a customer). Surface with context, let the PM judge.
- **Cross-project orphans.** `[prj-002:dec-001]` is an orphan if `prj-002` doesn't exist or `dec-001` isn't there. Only audit cross-references when the peer project is accessible.

## Output

A findings report, grouped by category, with specific paths and IDs. Zero writes.
