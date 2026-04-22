# JSONL Conventions

Rules for `core/decisions.jsonl` and `core/actions.jsonl`. Loaded by any skill that writes to or reads these files.

## File shape

- First line is always `{"_schema": { ... }}`. The harness skips it when processing entries.
- Every data entry has at minimum `id` and `when`. Other required fields are type-dependent (see below).
- Append-only. **Never edit or delete existing lines.** Mutations are expressed as new entries that reference the old via `from` or `retires`.
- Soft delete uses `"status": "archived"` — the line stays.
- Omit fields that don't apply. No `null`, no `""`, no `[]`.

## IDs

- Sequential, zero-padded to three digits: `dec-001`, `act-001`. Extend to four digits past 999.
- Scoped to the project folder. `dec-001` in project A is different from `dec-001` in project B.
- Always read the last ID in the target file before assigning a new one. Never guess.

## Timestamps

- Field name: `when`.
- Format: naive ISO 8601, KST implied: `2026-02-20T14:30:00`. No `+09:00` suffix — see `timestamps.md`.
- Minute precision is enough. Seconds can be `:00`.
- `when` records when the event occurred, not when it was logged (use the meeting time for events extracted from a meeting).

## Reference fields

Three fields, each answering a distinct question. No overlap.

| Field | Question | Shape |
| --- | --- | --- |
| `from` | Why does this entry exist? | single wikilink OR bracket ID |
| `links` | What else is relevant? | array, mixed wikilinks + bracket IDs |
| `retires` | What does this entry make inactive? | array of same-schema bracket IDs |

Format contract:
- Wikilinks `[[path]]` reference files (MD, YAML). Obsidian resolves them.
- Bracket IDs `[prefix-NNN]` reference JSONL entries or MD entities by `id`. Known prefixes: `dec-`, `act-`, `req-`, `meet-`, `risk-`.
- Linear ticket IDs (e.g. `FDSE-1509`) are **bare tokens**, never wrapped in single brackets. See `linear-tickets.md`.
- `[prj-NNN:prefix-NNN]` references an entity in another project.

Choose the right field:
- An action created in a meeting → `from: "[[meetings/...]]"`.
- A `task-done` completing a prior `task-created` → `from: "[act-NNN]"`.
- An action that implements a decision → `links: ["[dec-NNN]"]` (decision bracket ID in links).
- A new decision that supersedes an old one → `retires: ["[dec-MMM]"]` on the new decision-made.

## `retires` is same-schema only

- A `dec-NNN` entry's `retires` contains only `[dec-NNN]` IDs.
- An `act-NNN` entry's `retires` contains only `[act-NNN]` IDs.
- Never put `[req-NNN]`, `[meet-NNN]`, or `[risk-NNN]` in any JSONL `retires`. MD entities retire through their own frontmatter (`status` / `when_resolved`).
- Within decisions, `retires` is further restricted: **`decision-made` → `decision-made` only**. Raised entries close via `from`; dropped entries are terminal.

## Decision types (decisions.jsonl only)

Every decisions.jsonl entry carries `type`. Three values:

| Type | Body field | `from` | `retires` |
| --- | --- | --- | --- |
| `decision-raised` | `question` (required) | optional (usually a meeting) | never |
| `decision-made` | `decision` (required) | optional; may point to the raised entry it resolves | optional, made→made only |
| `decision-dropped` | `decision` (optional short label) | **required**, must point to `[dec-NNN]` of the raised entry being dropped | never |

Fields for decisions.jsonl: `id`, `type`, `when`, `question` | `decision`, `context`, `who`, `checked` (optional array), `from`, `links`, `retires`. See `filing-triggers.md` for "is this a decision-raised or a decision-made" judgment.

## Action types (actions.jsonl only)

Every actions.jsonl entry carries `type`. Seven values:

`task-created | task-done | task-blocked | communication | milestone | milestone-shifted | note`

Fields: `id`, `when`, `type`, `what`, `who`, `from`, `links`, `retires`.

Lifecycle patterns:
- Simple completion: `task-done` with `from: "[act-NNN]"` pointing to the original `task-created`.
- Block-then-complete: later `task-done` points `from` to the original `task-created`, NOT the `task-blocked`.
- Block-then-replace: the replacement `task-created` has `retires: ["[act-created]", "[act-blocked]"]` — include BOTH. Missing either leaves ghosts.
- Milestone retires tasks: `{type: milestone, retires: ["[act-NNN]", ...]}` when reaching the milestone makes tasks obsolete.

`milestone-shifted`: the `what` field must contain old date, new date, and reason. The shifted milestone is referenced as `ms-NNN` inline in `what` (timeline IDs are not bracket IDs).

## Substance rule

Every entry must stand alone if every link broke. Not `"See Slack thread"` — actually summarize what the decision was and why. Links are finding-aids, not the substance.

## Cross-schema discipline (the weak link)

When a `decision-made` spawns actions, include the decision's bracket ID in each resulting action's `links` array. The schema supports it; the practice needs reinforcement. The curation skill is the enforcement point — check before writing.

## Validation checklist before writing

- [ ] Last `id` in the file was read, new id is `previous + 1`.
- [ ] Type-specific required fields are present (see type tables above).
- [ ] `when` is naive ISO 8601 (`YYYY-MM-DDTHH:MM:SS`, no offset).
- [ ] Names in `who` and `checked` match `team.yaml` or `contacts.yaml` exactly.
- [ ] No empty strings, no empty arrays, no nulls.
- [ ] `retires` entries are same-schema bracket IDs.
- [ ] For `decision-made` that resolves a raised question: `from` points to `[dec-NNN]` of the raised entry.
- [ ] For `decision-dropped`: `from` is present and points to the raised entry being dropped.
- [ ] Every action that came from a decision has that decision's bracket ID in `links`.
