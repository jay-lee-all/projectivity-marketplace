# Edit Discipline

Rules for the `edit` skill: which fields are safe to mutate in place, which require supersede via `curate`, which are reference-fragile, and how a single PM-initiated change cascades into related writes. Loaded by every `edit` invocation. The vault's append-only intent is the right default; this file is the controlled escape hatch.

## Three buckets per target

Every field on every editable target falls into one of three buckets:

- **Hard-reject (immutable).** Identity anchors and semantic fields. Editing rewrites history or breaks bracket-ID resolution. The skill refuses and points the PM at the supersede pattern (file a new entry via `curate` with `retires: [<old-id>]`).
- **Refuse (reference-fragile).** Fields used as resolution keys across the whole vault — currently only `name` in `team.yaml` and `contacts.yaml`. The skill refuses with explanation. Renames are vault-wide refactors, not single edits.
- **Editable (whitelist).** Free-edit under PM confirmation. Some fields require a reason to be logged; see "Reason-required edits" below.

## Whitelist matrix

| Target | Hard-reject | Refuse (reference-fragile) | Editable |
|---|---|---|---|
| `decisions.jsonl` line | `id`, `type`, `when` (date part), `question`, `decision` | — | `who`, `checked`, `from` (with reason), `links` (additive only), `context`, `retires` (additive only), `status: archived`, `when` (time part, same calendar day) |
| `actions.jsonl` line | `id`, `type`, `when` (date part), `what` | — | `who`, `from` (with reason), `links` (additive only), `retires` (additive only), `status: archived`, `when` (time part, same calendar day) |
| `meetings/*.md` frontmatter | `id`, `when`, `type` | — | `title`, `who` (organizer; must be in `attendees` after edit), `attendees` (add/remove), `project` (warn — moving meetings between projects is rare) |
| `requirements/*.md` frontmatter | `id`, `when_created` | — | `title`, `status` (with cascade), `who`, `when_completed` (auto-set on `status: done`, auto-cleared on backwards transition) |
| `risks/*.md` frontmatter | `id`, `when_surfaced` | — | `title`, `who`, `category` (logged), `when_resolved` (with cascade) |
| `timeline.yaml` entries | `id` (`ms-NNN`, `dl-NNN`) | — | `when`, `title`, `description`, `completed`, `dropped_on`, `date`, `what`; bucket moves (milestones ↔ done ↔ dropped, with cascade) |
| `team.yaml` entry | — | `name` | `korean_name`, `email`, `slack`, `slack_name`, `github`, `linear`, `role`, `org` |
| `contacts.yaml` entry | — | `name` | `korean_name`, `email`, `slack`, `slack_name`, `github`, `linear`, `role`, `org` |

### `links` and `retires` are additive only

Edit can append new bracket IDs or wikilinks to `links` / `retires`. It cannot remove existing entries — those represent connections that existed at filing time, and removal is a quiet rewrite.

### `from` is single-valued; replacement is rewriting

The retrofit case is real (a meeting MD lands after the decision was filed from a Slack share). Edit allows replacing `from`, but always with a PM-supplied reason logged to `core/edits.jsonl`. Prefer adding the new pointer to `links` instead when the original `from` is still meaningful.

### `when` time-part vs date-part

Edit allows fixing the time portion of a `when` field (e.g. `2026-04-15T11:00:00` → `2026-04-15T11:30:00`) on the same calendar day — that's a typo class. Cross-day shifts are semantic (event ordering changes); reject and route to supersede.

## Out of scope for `edit`

| Operation | Right verb |
|---|---|
| Add a new project, requirement, risk, meeting, team member, contact | `scaffold` |
| File a new decision/action from a source | `curate` |
| Supersede a `decision-made` (intent reversed in a later meeting) | `curate` (file new `decision-made` with `retires: [dec-NNN]`) |
| Edit MD body prose (Spec text, meeting notes, free-form risk paragraphs) | PM edits the file directly; no skill needed |
| Hard delete an entry | Never. Use soft-retire markers below |

## Soft-retire only — never hard delete

| Subject | Soft-retire |
|---|---|
| Person no longer on team | Set `role: alumni` on their `team.yaml` entry. Historical `who` references stay resolvable |
| Milestone cancelled | Bucket move to `dropped:` with `dropped_on` date |
| Requirement no longer needed | Frontmatter `status: retired` (or `descoped` / `deferred` per intent) |
| Risk no longer relevant | Set `when_resolved` with a `## Resolution` line stating "no longer applicable" + reason |
| JSONL entry filed in error | `status: "archived"` on the line. The line stays — this is a soft delete only |

## Cascade rules

A single PM-initiated edit may require derived writes for vault consistency. Edit computes the full cascade, presents it as one diff plan, and writes everything atomically after one PM confirmation. The pattern mirrors `curate`'s "one source → multiple writes."

| Edit | Derived writes (cascade) |
|---|---|
| `decisions.jsonl` `from` replaced | log to `edits.jsonl` with reason; no other propagation |
| `decisions.jsonl` `links` add | verify each new target resolves (`link_graph.py`); reject if dangling |
| `decisions.jsonl` `retires` add | verify each retired target exists and is `decision-made`; reject otherwise |
| `decisions.jsonl` `status: archived` | warn if any other entry references this in `links`/`retires`; PM decides whether to also archive those |
| `actions.jsonl` `links` / `retires` / `status: archived` | same shape as decisions, with `act-NNN` schema |
| `requirements/*.md` `status: in-progress` | append dated line to `## Updates` |
| `requirements/*.md` `status: done` | set `when_completed = now()`; append `## Updates` line; **prompt** about open `task-created` actions tagged with this requirement (offer to file `task-done`) |
| `requirements/*.md` `status: retired` / `descoped` / `deferred` | append `## Updates` line; ask PM for replacement bracket; insert `Replaced by [[...]]` body line if supplied |
| `requirements/*.md` `status` backwards (e.g. `done` → `active`) | require reason; log to `edits.jsonl`; clear `when_completed`; append `## Updates` line citing reason |
| `risks/*.md` `when_resolved` set (was empty) | append `## Resolution` heading + line referencing the resolving event (PM supplies bracket ID); category is preserved |
| `risks/*.md` `when_resolved` cleared (re-open) | require reason; log to `edits.jsonl`; remove `## Resolution` section |
| `risks/*.md` `category` change | log to `edits.jsonl` (categorization shifts are signals worth tracking) |
| `timeline.yaml` mark milestone done | move entry from `milestones:` to `done:` with `completed: <date>`; **append `act-NNN` of `type: milestone`** to `actions.jsonl` with `links: [ms-NNN]` and `what` describing the completion |
| `timeline.yaml` shift milestone date | update `when:`; **append `act-NNN` of `type: milestone-shifted`** with reason in `what` (reason required; `what` must contain old date, new date, reason — see `jsonl.md`) |
| `timeline.yaml` drop milestone | move to `dropped:` with `dropped_on: <date>`; **append `act-NNN` of `type: note`** with reason (reason required) |
| `timeline.yaml` add milestone | allocate next `ms-NNN`; insert into `milestones:`; no JSONL cascade (proactive add ≠ event) |
| `timeline.yaml` add deadline | allocate next `dl-NNN`; insert into `deadlines:`; no JSONL cascade |
| `team.yaml` / `contacts.yaml` field change | log to `edits.jsonl`; no cross-file propagation (refs use `name`, which is locked) |

Write order in cascades: the structured target first, then derived JSONL appends, then `## Updates` / `## Resolution` body sections, then the `edits.jsonl` log entry. If any pre-validation fails, the whole cascade is rejected; partial writes never land.

## Reason-required edits

The PM must supply a one-line reason for these. The reason is logged to `core/edits.jsonl`.

- `decisions.jsonl` / `actions.jsonl` `from` replacement (any non-empty → any other value)
- Requirement `status` backwards transition (`done` → `active|in-progress`, `retired` → anything other than retired/descoped/deferred is rejected outright)
- Risk `when_resolved` cleared (re-open)
- Timeline `milestone-shifted` (the reason becomes part of the cascaded action's `what`)
- Timeline milestone dropped (the reason becomes part of the cascaded `note` action's `what`)

All other whitelist edits log without a reason.

## `core/edits.jsonl` schema (`edits-v1`)

Opt-in audit log. Created lazily by `append_edit_log.py` on the first edit a project receives. `scaffold` does not pre-create it. `audit` reads it if present, treats absence as "no edits yet."

First line:
```
{"_schema": "edits-v1"}
```

Entry shape:
```json
{
  "id": "edit-001",
  "when": "2026-04-24T15:30:00",
  "who": "Jay Lee",
  "target_file": "projects/jobis/core/decisions.jsonl",
  "target_id": "dec-042",
  "field": "from",
  "before": "https://allganize.slack.com/archives/...",
  "after": "[[meetings/2026-03-12-jobis-kickoff]]",
  "reason": "Backfilled meeting MD"
}
```

Field rules:
- `id` — sequential `edit-NNN`, allocated by `next_id.py --jsonl <core/edits.jsonl>`.
- `when` — naive ISO 8601 KST, the moment the edit was applied (not the event the edit refers to).
- `who` — the PM running the edit, resolved against `team.yaml` (passed via `--actor` to `append_edit_log.py`).
- `target_file` — vault-relative path of the file mutated. For cascades, log one entry per logical edit (the user's intent), not one per cascaded write.
- `target_id` — the entry id touched (`dec-NNN`, `act-NNN`, `req-NNN`, `risk-NNN`, `meet-NNN`, `ms-NNN`, `dl-NNN`, or a `name` for team/contacts).
- `field` — the field name.
- `before` / `after` — JSON values (strings, arrays, etc.). For `links` additions, `before` is the old array and `after` is the new array.
- `reason` — required for the edits in the "Reason-required edits" section above. Optional otherwise (omit field, do not write empty string).

## Confirmation flow

The skill builds a diff preview per `templates/edit-diff.md`, shows the full cascade in one block, and writes nothing until the PM approves. The PM can accept, reject, or edit any part of the plan — same mechanic as `curate`. After approval, writes happen in cascade order using the atomic mutator scripts; verification runs immediately after.

## Validation discipline

- Every JSONL line that edit produces (cascaded actions, edited lines) must pass `validate_jsonl.py --line <json> --kind <kind>` before the diff is shown.
- Every YAML mutation must reload-and-parse cleanly in memory before write.
- Every MD frontmatter mutation must round-trip through `frontmatter_index.py` after write — confirm the entry still resolves with the expected fields.
- Every `who` / `attendees` value must resolve via `resolve_name.py` — unresolved tokens are surfaced to the PM, never silently filed.
- Post-write: `reconcile_cross_refs.py --project <slug>` must report no new orphans introduced by the edit.
