---
description: Mutate existing vault entries — JSONL line corrections, MD frontmatter changes, timeline.yaml operations, team/contacts.yaml field updates — with whitelist enforcement, cascade computation, atomic writes, and an audit log. Use when a target needs to change ("fix the owner on dec-042", "mark ms-003 done", "Sarah moved to engineering", "now that meet-018 exists, link it as the source for dec-042"). One PM-initiated change becomes one edit + its cascade in a single confirmation. Hard-rejects identity/semantic field edits and points at the supersede pattern via curate.
hooks:
  - conventions/edit-discipline.md
  - conventions/references.md
  - conventions/timestamps.md
---

# edit — target-driven mutation with cascade

## When to Use

A specific target needs to change and there is no source driving it. Typical triggers:

- Backfilling a `from` reference on an old `decision-made` after the meeting MD finally lands.
- Marking a milestone done that was missed in real-time (`ms-003 done as of 2026-04-15`).
- Correcting a typo in `who` after a Slack ID failed to resolve at curate time.
- Marking a requirement `done` and propagating to its open `task-created` actions.
- Updating a person's role in `team.yaml` when they switch teams.
- Resolving a risk and writing the `## Resolution` marker.
- Adding a new milestone or deadline proactively (PM-known, not source-driven).

Do **not** use this skill to:

- Add a new project, requirement, risk, meeting, team member, or contact → that's `scaffold`.
- File a new decision/action from a source (Slack thread, meeting, Linear export) → that's `curate`.
- Supersede a `decision-made` (intent reversed in a later meeting) → file a new `decision-made` with `retires: [dec-NNN]` via `curate`.
- Edit MD body prose freely — only structured body sections (`## Updates`, `## Resolution`) are written by edit, as part of a cascade. Free-form prose stays a direct PM edit.
- Hard-delete anything → use the soft-retire markers in `edit-discipline.md`.

## Conventions

Frontmatter `hooks` declares the always-load set: `edit-discipline.md`, `references.md`, `timestamps.md`. The whitelist matrix and cascade rules are authoritative in `edit-discipline.md`; do not restate them here.

**Conditionally load** when the edit touches an entity type:

- `conventions/jsonl.md` — JSONL line edit on `decisions.jsonl` / `actions.jsonl`.
- `conventions/md-meetings.md` — meeting frontmatter edit.
- `conventions/md-requirements.md` — requirement frontmatter or `## Updates` cascade.
- `conventions/md-risks.md` — risk frontmatter or `## Resolution` cascade.
- `conventions/linear-tickets.md` — when adding a Linear-shape token to `links`.

## Workflow

1. **Parse intent.** From the PM's request, extract the target file and the field(s) being changed. If multiple entries match (e.g. PM said "the kickoff meeting" and there are two), use `AskUserQuestion` to disambiguate.

2. **Verify the target exists.** Pick the right reader for the kind:
   - JSONL line: grep the file by id.
   - MD frontmatter: `python "$CLAUDE_PLUGIN_DIR/scripts/frontmatter_index.py" <folder> --filter id=<id>`.
   - YAML record: parse the file and look up by `name`.
   - Timeline entry: load `timeline.yaml`, scan all four buckets.

   Missing target → decline with the right verb (route to `scaffold` for adds, `curate` for source-driven).

3. **Whitelist check** against `edit-discipline.md`:
   - Hard-reject (immutable identity/semantic field) → refuse with the supersede pointer: "this is a semantic change; file a new `decision-made` with `retires: [<id>]` via `/projectivity:curate`."
   - Refuse (reference-fragile, currently `name` in team/contacts) → explain why (vault-wide resolution key) and stop.
   - Editable → continue.

4. **Resolve names.** Any new `who`, `attendees`, or `checked` value goes through `resolve_name.py`:
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/resolve_name.py" "<token>" \
     --team "<vault>/team.yaml" --contacts "projects/<slug>/core/contacts.yaml"
   ```
   Unresolved → ask the PM (offer to add the person via `/projectivity:scaffold`); never silently file raw IDs.

5. **Compute cascade.** Look up the edited field in the cascade table in `edit-discipline.md`. Build the full set of derived writes:
   - Cross-reference checks via `link_graph.py` (e.g. proposed `links` targets must resolve).
   - Cascaded JSONL appends (e.g. `mark ms-003 done` → also append an `act-NNN` of `type: milestone`). Allocate the new id via `next_id.py --jsonl projects/<slug>/core/actions.jsonl`.
   - Cascaded body sections (e.g. requirement `status: done` → append a `## Updates` line).
   - Prompted cascades (e.g. requirement done → search for open `task-created` actions tagged with this requirement; ask the PM via `AskUserQuestion` whether to also file `task-done`).

6. **Determine if a reason is required.** Per `edit-discipline.md` "Reason-required edits": `from` replacement, requirement backwards-status transitions, risk re-open (clear `when_resolved`), milestone shift, milestone drop. If required and not yet supplied, ask the PM with `AskUserQuestion`.

7. **Pre-validate every proposed write.**
   - JSONL lines (the edited line and any cascaded appends):
     ```bash
     python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" \
       --line '<proposed-json-line>' --kind decisions
     ```
   - YAML mutations: parse the proposed result in-memory before disk write — `update_yaml_field.py` and `timeline_ops.py` both reload-and-validate internally, but the skill should mentally model the result first.
   - MD frontmatter changes: prepare the `--set` / `--json-set` arguments so the edit is unambiguous.

   Any pre-validation failure → revise the plan; do not show a known-broken plan to the PM.

8. **PM confirmation — mandatory, unified.** Render the diff plan per `templates/edit-diff.md`. Show the original edit + every cascaded write in one block. The PM can accept, reject, or revise any part. Write nothing until approval.

9. **Write atomically, in cascade order.** Pick the script per write kind:

   | Write kind | Script |
   |---|---|
   | JSONL line correction (existing entry) | `update_jsonl_line.py --file <core/...jsonl> --id <id> --json '<new-line>'` |
   | New JSONL line (cascaded action — milestone done / shifted / dropped) | atomic append via Python (read-all + append-validated-line + `atomic_write` from `_common.py`); pre-validate the line with `validate_jsonl.py --line` first |
   | MD frontmatter + optional body section | `update_frontmatter.py --file <md> --set k=v ... [--append-body '<Updates line>']` |
   | timeline.yaml structured op | `timeline_ops.py --mark-done|--shift|--drop|--add-milestone|--add-deadline|--edit-deadline|--edit-milestone-field --file <timeline.yaml> ...` |
   | team.yaml / contacts.yaml field set | `update_yaml_field.py --file <yaml> --select name=<X> --field <f> --value <new>` |
   | edits.jsonl audit log line | `append_edit_log.py` (step 10) |

   Order within a cascade: structured target first (e.g. timeline.yaml move), then derived JSONL appends, then any `## Updates` / `## Resolution` body section appends. If any write's pre-validation fails, abort the entire cascade — no partial writes land. Each individual file write is atomic via temp-file-rename, so a filesystem-level interruption leaves files either fully old or fully new, never half-written.

10. **Log to `core/edits.jsonl`.** One entry per logical PM intent (not per cascaded write):
    ```bash
    python "$CLAUDE_PLUGIN_DIR/scripts/append_edit_log.py" \
      --project <slug> --actor "<PM name>" \
      --target-file "projects/<slug>/core/decisions.jsonl" \
      --target-id "dec-042" --field "from" \
      --before-json '"https://allganize.slack.com/..."' \
      --after-json '"[[meetings/2026-03-12-jobis-kickoff]]"' \
      --reason "Backfilled meeting MD"
    ```
    `append_edit_log.py` lazy-creates `core/edits.jsonl` on first call. Reason argument required only for the edits listed in `edit-discipline.md`.

11. **Post-write verification.** Always:
    ```bash
    python "$CLAUDE_PLUGIN_DIR/scripts/reconcile_cross_refs.py" --project <slug>
    ```
    No new orphans. Plus, for any modified JSONL file:
    ```bash
    python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/decisions.jsonl"
    ```
    Exit 0 means clean. Anything else → surface immediately to the PM, do not silently retry.

12. **Output.** List every file touched with its path, the `edit-NNN` id(s) logged, the verification results, and any PM follow-ups (e.g. "you re-opened risk-007 — consider editing the related decisions").

## Gotchas

- **`from` is single-valued; replacement is rewriting.** Always require a reason; logged to `edits.jsonl`. When the original `from` is still meaningful, prefer adding the new pointer to `links` instead of replacing `from`.
- **`when` time-part edit only on the same calendar day.** Cross-day shifts change event order; reject as a semantic change and route to supersede via `curate`.
- **`links` and `retires` are additive only.** Edit can append, never remove. Removing a connection that existed at filing time is rewriting — file a new entry via `curate` if the relationship genuinely changed.
- **Milestone-done cascade is two-half: timeline.yaml + actions.jsonl.** If the action append fails validation, abort the timeline mutation too — never leave the two halves out of sync. Each individual file write is atomic; the skill enforces transactional intent across files by validating *all* proposed writes before any of them execute.
- **Backwards status transitions are a smell.** `done` → `active` always requires reason. `retired` → anything other than retired/descoped/deferred is rejected outright; retirement is final, scaffold a new requirement instead.
- **Hard delete is never offered.** Use the soft-retire markers from `edit-discipline.md`: `role: alumni` (people), bucket move to `dropped:` (milestones), `status: retired` (requirements), `when_resolved` with note (risks), `status: archived` (JSONL lines).
- **Adds are scaffold's job.** "Add Meera to team.yaml" → decline, suggest `/projectivity:scaffold`. "Add a new requirement" → same. Edit is modify-existing only.
- **Body edits are out of scope.** PM hand-edits free-form prose. Edit only writes structured body sections (`## Updates`, `## Resolution`) as part of cascades, via `--append-body` on `update_frontmatter.py`.
- **`edits.jsonl` is opt-in and lazy.** First edit creates it with the `_schema` line. `audit` checks-if-present, doesn't require it. `scaffold` does not pre-create it.
- **Atomic writes only.** All five edit-skill mutator scripts use the shared `atomic_write` helper from `_common.py` (temp file + fsync + `os.replace`). Crash-mid-write cannot corrupt vault state. The existing `update_curate_state.py` keeps its direct-overwrite (curate-state is regenerable).
- **Get "now" from the shell, not training data.** When setting `when_completed`, `when_resolved`, or any timestamp the edit cascade needs:
  ```bash
  python -c "from datetime import datetime, timezone, timedelta; print(datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%dT%H:%M:%S'))"
  ```
- **One edit log entry per logical intent, not per cascaded write.** A milestone-done that touches timeline.yaml + actions.jsonl logs one `edits.jsonl` line, not two. The audit story is "what did the PM mean to do," not "which files were touched."

## Verification

Run before declaring done. Same philosophy as curate: cheaper to catch a bad write here than to let `audit` surface it later.

1. **Re-validate every modified JSONL file.**
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/actions.jsonl"
   ```
   Exit 0 means clean. Non-zero is a bug introduced by this edit — surface to the PM.

2. **Cross-references resolve.** `reconcile_cross_refs.py --project <slug>` reports zero new orphans. If the edit added a bracket ID to `links`, confirm the target exists via `link_graph.py <target-id> --project <slug>`.

3. **Edit log entry landed.** `core/edits.jsonl` has the new `edit-NNN` line with the right `target_file`, `target_id`, `field`, `before`, `after`, and (if required) `reason`.

4. **No stale `.tmp` files.** Atomic writes use `<file>.tmp` then `os.replace`. After a successful edit, no `.tmp` should remain in the vault. If one does, a write was interrupted — investigate.

## Output

A structured report: every file touched (with path), the `edit-NNN` id(s) logged, verification results from steps 1–4, and any PM follow-ups (e.g. "you re-opened risk-007; consider revisiting [dec-019] which was filed when this risk was thought resolved").
