---
description: Read-only integrity check across a project vault — schema violations, orphan references, stale raised decisions, aging risks, thin MDs, name inconsistencies. Use weekly, before a release, or after heavy curation: "audit the vault", "what's broken in Project_OS", "check for orphans". Never auto-fixes — reports findings; the PM (or `curate`) acts on them.
hooks:
  - conventions/jsonl.md
  - conventions/references.md
  - conventions/timestamps.md
  - conventions/linear-tickets.md
  - conventions/md-meetings.md
  - conventions/md-requirements.md
  - conventions/md-risks.md
  - conventions/project-shape.md
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

## Conventions

Frontmatter `hooks` declares the full convention set — audit inspects every entity type, so it loads everything: `jsonl.md`, `references.md`, `timestamps.md`, `linear-tickets.md`, `md-meetings.md`, `md-requirements.md`, `md-risks.md`, `project-shape.md`.

## Workflow

1. **Scope the audit.** Per-project by default. Cross-project audit is a distinct invocation — confirm which with the PM if ambiguous.

2. **Canonical project shape.** For each `projects/<slug>/` in scope, verify every entry listed in `conventions/project-shape.md` exists: `overview.md`, the `core/` directory with its four files (`decisions.jsonl`, `actions.jsonl`, `timeline.yaml`, `contacts.yaml`), and the four content subfolders (`meetings/`, `requirements/`, `risks/`, `_files/`). A plain `ls` is sufficient — no script needed. Missing entries are **scaffold bugs**, not curation ones; flag under a dedicated report section (see step 10) so they route to the right fix. Empty subfolders are **not** findings — they're the contract.

3. **JSONL schema check.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/actions.jsonl"
   ```

   Non-zero exit means structural violations. List them verbatim — don't paraphrase.

4. **Orphan references.** One pass across the whole project:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/reconcile_cross_refs.py" --project <slug>
   ```

   Returns `defined_ids`, `references`, `orphans`, and `defined_but_unreferenced`. Every entry in `orphans` is a real finding — it names a target that's referenced somewhere but never defined. `defined_but_unreferenced` is informational (not every defined ID must have incoming refs; a newly-filed `decision-made` often has none yet).

   For a deep-dive on any single orphan (who points at it, what field, what context), `link_graph.py <id> --project <slug>` is the follow-up tool.

5. **Stale raised decisions.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/aging_pending.py" --project <slug> --threshold 30
   ```

   Surface anything older than 30 days with no `from`-closure. This is stricter than `brief`'s 14-day nudge — audit catches the long-forgotten ones.

6. **Open risks past category-specific thresholds.** Use `filter_by_age.py` — one call per category with its threshold:

   ```bash
   # Infrastructure / integration: > 14 days open
   python "$CLAUDE_PLUGIN_DIR/scripts/filter_by_age.py" \
     --folder "projects/<slug>/risks" --field when_surfaced \
     --min-days 14 --filter category=infrastructure --filter when_resolved=
   # Customer / process: > 30 days open
   python "$CLAUDE_PLUGIN_DIR/scripts/filter_by_age.py" \
     --folder "projects/<slug>/risks" --field when_surfaced \
     --min-days 30 --filter category=customer --filter when_resolved=
   ```

   `--filter when_resolved=` matches the empty string, i.e. still-open risks. Each call returns entries with `age_days` computed; no date arithmetic in-skill.

7. **Name consistency.** Run `resolve_name.py` over every `who` field in JSONL + every `attendees` entry in meeting MDs. Flag tokens that fall into the `unresolved` bucket or that resolve via different fields across files (e.g. one entry uses the Slack ID, another uses the name).

8. **Thin MDs.** Requirements with `status: active` but an empty Spec section. Risks with no Investigation section and `when_surfaced` older than 7 days. Heuristic, not strict — call these out as "likely thin" and let the PM decide.

9. **Temporary-mitigation drift.** Risks with `category: configuration` that have no reversion/formalization conditions in the body. The convention requires these; audit enforces.

10. **Report.** One grouped findings document:

    ```
    ## Canonical shape violations
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
- **Vault location.** Scripts use `$PROJECTIVITY_VAULT` or `cwd/Project_OS`. If they fail to find the project, fall back to `--path "<absolute>/projects/<slug>"`.

## Verification

The audit produces a report; the verification step makes sure the report itself is trustworthy:

1. **Every reported finding includes a path or bracket ID.** A finding without a locator ("there are some orphans") is useless — the PM can't act on it. If your script output is missing locators, fix the script call (most accept identifying flags) before reporting.

2. **No section silently empty.** If "Orphan references" has zero findings, write `None.` rather than omitting the heading. Silent omission is indistinguishable from "I forgot to check that category" — both leave the PM unsure whether the system is healthy or whether the audit was incomplete.

3. **Script exit codes respected.** `validate_jsonl.py` returns 2 on failure with details on stderr. If you swallow stderr, the audit will report "no schema violations" while violations exist. Always capture and surface stderr for non-zero exits.

## Output

A findings report, grouped by category, with specific paths and IDs. Zero writes.
