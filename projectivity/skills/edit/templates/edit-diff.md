# Edit Diff Preview — format for PM confirmation

The diff plan that `edit` shows the PM before any file is written. One block covers the original edit and every cascaded write so the PM can review the full intent in a single pass. Keep section order stable; PMs get faster at reviewing when sections always appear in the same place. Omit a section entirely if it has no entries — but keep a one-line `None.` if you actively checked and decided nothing should fire there. Silent omission looks like forgetting.

## Format

```
## Intent

<one sentence in the PM's own words: "Mark ms-003 done as of 2026-04-15.">

## Reason
(Required for: from replacement, requirement backwards-status transitions, risk re-open, milestone shift, milestone drop. Otherwise omit this section entirely — not even a `None.` line.)

<one-line PM-supplied reason, exactly as it will be logged to edits.jsonl>

## Primary edit

- target: <vault-relative path>:<id> (or <field> for YAML records)
  field: <field name>
  before: <old value, JSON-rendered>
  after:  <new value, JSON-rendered>

(For multi-field edits on the same target — e.g. requirement status: done sets both status and when_completed — list each field on its own indented block under one target line.)

## Cascade

(List every derived write in the order it will execute. If there are none, write `None.` — and do *not* omit the heading; cascades are the differentiator from a raw text edit, so the PM should always see whether one fired or not.)

- <file path>: <what changes>
  detail: <one or two lines describing the write — e.g. "append act-094 of type: milestone with links: [ms-003]">

- <file path>: <what changes>
  detail: <...>

## Validation

- JSONL lines pre-validated: <count> / <count> via validate_jsonl.py --line
- Cross-reference targets resolve: <count> / <count> via link_graph.py
- Names resolved via resolve_name.py: <count> / <count>

(All three lines should read N/N — any X/N where X<N is a blocker; surface it before asking for approval.)

## Edit log

- target_file: <vault-relative path>
- target_id: <id>
- field: <field>
- before: <JSON-rendered>
- after:  <JSON-rendered>
- reason: <if required, else omit this line>

(One edits.jsonl entry per logical PM intent, not per cascaded write. The cascaded action append from a milestone-done is part of the cascade; it does not get its own edit log entry.)

## Confirmation

Apply this edit and its cascade? (y/n)
```

## Notes for the skill

- The diff is presented as one block; the PM approves once for the whole thing. Partial approval ("yes to the timeline change but not the action append") means the cascade is broken — either edit the cascade rule or reject the whole plan and start over.
- Render `before` / `after` as compact JSON when they're scalar or short; multi-line YAML-style is fine for objects with more than two fields.
- `Validation` line counts must be from actual script invocations performed *before* the diff is shown — never claim N/N optimistically.
- For cascades that prompt the PM mid-plan (e.g. "you marked req-005 done; here are 3 open task-created actions tagged with this requirement — close any?"), resolve the prompt *before* rendering the final diff. The diff shown to the PM is the post-prompt full plan, not a half-formed draft.
- `Reason` text appears verbatim in `edits.jsonl` and (for milestone-shifted / dropped) in the cascaded action's `what` field. Encourage the PM to write it as a sentence the future-PM auditing the log will understand.
