# Curate Proposal Preview — format for PM confirmation

The unified plan that `curate` shows the PM before any file is written. One block covers every proposed entity across all types so the PM can review cross-references and filing decisions in a single pass.

The format below is the contract. Keep section order stable; PMs get faster at reviewing when sections always appear in the same place. Omit a section entirely if it has no entries — but keep the heading and say `None.` to make it clear you checked. Silent omission looks like forgetting.

## Format

```
## Low-confidence items
(Only present on `--backfill` runs that produced flagged items — otherwise omit this section entirely, headers and all. Lists items any subagent marked as ambiguous judgment calls: "decision or risk?", unresolved names, temp-mitigation language the subagent wasn't sure how to categorize. PMs skim here first; the rest of the plan is "trust and approve.")

- [<bracket-id>] (<what-kind>): <one-line description>
    flagged by: window <N>
    reason: <what the subagent was uncertain about>
    proposed filing: <how the subagent ultimately filed it — PM can accept, edit, or override>

## Source(s)

- <one line per source>: meeting MD path, Slack thread identifier, Linear export range, email from-date, or "manual notes".

## Meeting MD
(None, an existing [[meetings/YYYY-MM-DD-slug]] the source already references, or a new one from the `meeting` skill that precedes this curation)

## Decisions

- [dec-NNN] (decision-raised): <question>
    from: [[meetings/...]]         ← or the Slack link / Linear ref
    who: <raiser>
    checked: [<reviewers>]         ← optional
    links: [<related bracket IDs or wikilinks>]   ← optional; omit when empty

- [dec-NNN] (decision-made): <decision>
    from: [dec-MMM]                ← when resolving a raised entry; else [[meetings/...]]
    who: <decider>
    context: <one or two sentences>
    retires: [[dec-XXX], ...]      ← only when superseding prior decision-made; omit otherwise
    links: [...]                   ← optional

- [dec-NNN] (decision-dropped): <brief note on why>
    from: [dec-MMM]                ← mandatory: points to the raised entry being closed
    who: <decider>

## Actions

- [act-NNN] (task-created): <what>
    who: <owner>
    from: [[meetings/...]] or [dec-NNN]
    links: [<optional>]

- [act-NNN] (communication): <what>
    from: <source>
    links: [<contact wikilink or customer reference>]

- [act-NNN] (note): <what>
    from: [[meetings/...]]         ← optional

## Timeline updates

- ms-NNN: moved to `done:`, completed: YYYY-MM-DD (driven by [act-NNN])
- ms-NNN: `when:` shifted YYYY-MM-DD → YYYY-MM-DD (driven by [act-NNN])

(Omit the section entirely if the plan has no `milestone` or `milestone-shifted` actions — same rule as other empty sections in this template.)

## Requirement updates

- [[requirements/<slug>]]: <field change> — e.g. status `active` → `in-progress`
    driven by: [dec-NNN] or [[meetings/...]]
    body addition: <Updates-section line that will be appended>

- [[requirements/<slug>]]: new
    id, title, status, who, when_created: <as drafted>
    body: Spec skeleton from `md-requirements.md`

## Risks

- [[risks/<slug>]] (new): <title>
    category: <infrastructure / model / integration / configuration / customer / process>
    when_surfaced: <now, naive ISO 8601 — see conventions/timestamps.md>
    who: <surfacer>
    opening line: <one sentence>
    reversion conditions: <only for category: configuration — per filing-triggers.md>

- [[risks/<slug>]] (update): <brief description of what's being added>
    body addition: <Investigation paragraph or Resolution text>
    frontmatter change: `when_resolved` filled, or nothing

## Unresolved / uncertain

- <tokens that didn't resolve via resolve_name.py>
- <filing calls Claude wasn't sure about — e.g. "is this a risk or a decision-raised?" per filing-triggers.md>
- <aging-pending decisions the PM should see before adding new raised entries>

## Aging-pending nudge
(If adding any new decision-raised entries — SKILLS-GUIDE requires surfacing existing aging entries first so the PM can close or merge instead of double-filing. Results from `aging_pending.py --threshold 14` go here.)
```

## Notes for the skill

- Every bracket ID in the plan must come from `next_id.py`, not invented. If the plan shows `[dec-042]` pointing at `[dec-041]`, allocate 041 first.
- Every JSONL line in the plan should pre-validate via `validate_jsonl.py --line ... --kind decisions|actions`. Flagging errors at the plan stage is cheaper than after the write.
- Write order at confirmation time: meeting MD (if new) → decisions → actions → `timeline.yaml` updates (for any `milestone` / `milestone-shifted` action) → requirement updates → risk MDs. Cross-references resolve cleanly because dependencies exist first.
- Any `milestone` / `milestone-shifted` action in the Actions section requires a matching Timeline updates entry — they're two halves of one change.
- `retires` appears only on `decision-made` entries targeting other `decision-made` entries and only on actions targeting other actions. Never on raised/dropped decisions; never targeting MD entities.
- **Backfill plans add a `## Low-confidence items` section at the top.** Normal (non-backfill) curate plans omit that section entirely — one source rarely produces enough ambiguity to warrant a dedicated top-of-plan callout. Backfill produces many entries across many windows, so concentrating the PM's review on flagged judgment calls keeps the skim-review tractable.
