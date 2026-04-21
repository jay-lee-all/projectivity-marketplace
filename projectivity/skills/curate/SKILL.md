---
description: Unified curation pass that turns a source (meeting MD, Slack thread, Linear dump, email, manual notes) into vault entries — decisions, actions, requirement updates, risks — in one consistent pass. Use after `meeting`, or any time a source has new signal: "file this thread", "log what came out of the call", "add a risk for the temporary rate-limit". One confirmation plan; nothing written until PM approves.
hooks:
  - conventions/filing-triggers.md
  - conventions/jsonl.md
  - conventions/references.md
  - conventions/timestamps.md
  - conventions/linear-tickets.md
---

# curate — source → vault entries

## When to Use

A source has new signal that should land in the vault: a just-written meeting MD, a Slack thread the PM pasted in, a Linear export, an email chain. One source typically produces multiple entity types (decisions + actions + risks); this skill handles all of them in one pass so cross-references are consistent.

Do **not** use this skill to:

- Create a meeting MD from a transcript — that's `meeting`.
- Edit an existing requirement or risk outside the context of a source — read and edit directly.
- Scaffold new structure — that's `scaffold`.

## Conventions

Frontmatter `hooks` declares the always-load set the resolver injects at skill start: `filing-triggers.md`, `jsonl.md`, `references.md`, `timestamps.md`, `linear-tickets.md`.

**Conditionally load** when the plan touches an entity type:

- `conventions/md-meetings.md` — if producing or updating a meeting MD.
- `conventions/md-requirements.md` — if touching requirements.
- `conventions/md-risks.md` — if surfacing or updating a risk.

The conventions are authoritative; do not restate their contents here.

## Workflow

1. **Read the source fully before filing anything.** Sources are often multi-threaded; a decision on line 40 may be dropped on line 80.

2. **Plan first, write second.** Build a full plan covering every proposed entity before writing any file. Ordering matters — cross-references depend on IDs existing.

   Follow the shape in [templates/proposal-preview.md](templates/proposal-preview.md). That's the format the PM sees at confirmation — keep sections in the same order so the review is predictable.

3. **Use filing-triggers guidance.** The "is this a decision or an action?" call is in `filing-triggers.md`; consult it. When uncertain, log it — audit filters noise later.

4. **Watch for temporary-mitigation language.** Trigger phrases: `일단 ~로 임시 상향`, `임시로 ~ 비활성화`, `workaround`, `hotfix`, `revert later`, `until we figure out a proper fix`. Any of these → open a risk MD with `category: configuration` and name the reversion conditions in the body. Do **not** skip because it feels ephemeral — the convention is explicit about this.

5. **Assign IDs in order.** For each JSONL-backed entry, get the next ID first:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --jsonl "projects/<slug>/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --jsonl "projects/<slug>/actions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --folder "projects/<slug>/risks" --prefix risk-
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --folder "projects/<slug>/requirements" --prefix req-
   ```

   Allocate sequentially within the plan so `[dec-042]` pointing at `[dec-041]` is consistent before any file is written.

6. **Resolve people.** Any `who`/`attendees`/Slack-ID token goes through `resolve_name.py`. Unresolved tokens are surfaced to the PM during confirmation, never silently filed as raw IDs.

7. **Validate JSONL lines before presenting them.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" \
     --line '<proposed-json-line>' --kind decisions
   ```

   Fix any errors before the confirmation step.

8. **PM confirmation — mandatory, unified.** Present the full plan (meeting, decisions, actions, requirements, risks) in one block. The PM can accept, reject, or edit any part. Write only after approval.

9. **Write in dependency order:** meeting MD (if any) → decisions → actions → requirement updates → risk MDs. Cross-references resolve cleanly because dependencies exist first.

10. **Post-write summary:** list every file touched with its path, and surface any `unresolved` tokens or uncertain filings for the PM to follow up on.

## Gotchas

- **Raised then made in the same source.** Don't file both `decision-raised` and `decision-made` — if the question was asked and answered in the same meeting, file only the `decision-made`. `from` points to the meeting wikilink, not a non-existent raised entry.
- **`retires` rules are strict.** `decision-made` → `decision-made` only. Actions.retires → `[act-NNN]` only. **Never** target MD entities (`[req-NNN]`, `[risk-NNN]`, `[meet-NNN]`) in any `retires` array — MDs retire via frontmatter. The validator catches this, but the plan shouldn't propose it.
- **Linear tickets are bare tokens.** `FDSE-1509`, not `[FDSE-1509]`. Place them inline in `context`/`what` or in `links` arrays as plain strings.
- **KST everywhere.** Every JSONL `when` ends in `+09:00`. Meeting dates are date-only. Get "now" from the shell, not from training data:

  ```bash
  python -c "from datetime import datetime, timezone, timedelta; print(datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%dT%H:%M:%S+09:00'))"
  ```

- **Milestone shifts vs. trivial date tweaks.** Only log `milestone-shifted` when the shift has a reason worth preserving (scope change, blocker, customer request). Holiday reshuffles go directly to `timeline.yaml`.
- **Meetings don't enumerate outputs.** Decisions point to meetings via `from`; meetings don't list their decisions. Obsidian backlinks handle reverse lookup.
- **Vault location for scripts.** All script invocations resolve the project via `$PROJECTIVITY_VAULT` or `cwd/Project_OS`. If that fails, pass `--path "<absolute>/projects/<slug>"` instead of `--project <slug>`.

## Verification

Run before declaring done. The aim is to catch bad writes before the next skill consumes them — `audit` will surface them later, but cheaper to fix in the same session:

1. **Re-validate every JSONL line you wrote.** The pre-write check in step 7 covers proposed lines; this confirms what actually landed on disk:
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/actions.jsonl"
   ```
   Exit 0 means clean. Any non-zero is a bug introduced by the write — surface to the PM, don't silently retry.

2. **Cross-references resolve.** For every new bracket ID you set as a `from`/`links`/`retires` target, confirm the target exists. `link_graph.py <id> --project <slug>` is the cheapest way — if the target is missing, `incoming` will be empty for an ID you just wrote a reference to.

3. **No raised+made pair for the same question in one source.** Re-read your written decisions: if both a `decision-raised` and a `decision-made` carry `from` pointing at the same meeting and the made one resolves a question that wasn't asked elsewhere, you double-filed. The convention is "made-only when raised and made happen in the same source".

4. **Aging-pending nudge fired (if applicable).** If you added a new `decision-raised`, the SKILLS-GUIDE expects you to have shown the PM existing aging-pending decisions first (see `aging_pending.py --threshold 14`). Note in the output whether you did.

## Output

A structured plan shown to the PM (per `templates/proposal-preview.md`), then on approval: the list of files written with their paths, the verification results above, and any unresolved tokens or uncertain filings for the PM to follow up on.
