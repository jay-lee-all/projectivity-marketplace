# Meeting MD Conventions

Rules for `projects/{project}/meetings/{YYYY-MM-DD}-{topic-slug}.md`. Loaded by `meeting`, `curate`, and `audit`.

## Filename

- Format: `{YYYY-MM-DD}-{topic-slug}.md`. Date first for chronological sorting.
- Slug: short, English or Korean, lowercase, hyphen-separated. Examples: `2026-02-20-kickoff`, `2026-03-15-scope-review`, `2026-04-01-customer-uat`.
- **Never rename a meeting file after creation.** Wikilinks in other MDs update via Obsidian, but the stability principle is stronger than convenience.

## Frontmatter (required, 7 fields)

```yaml
---
id: meet-NNN
title: <human-readable title>
when: YYYY-MM-DD             # date only, no time, no timezone
type: customer | internal
who: <organizer, name from team.yaml>
attendees: [<name>, <name>, ...]
project: <project folder name>
---
```

- `id` is stable across renames. Bracket IDs like `[meet-001]` resolve to this.
- `title` is what a PM would call this meeting in conversation. Matches or closely matches the filename slug.
- `when` is date-only. Minute-precision `when` for events *inside* the meeting goes on JSONL entries, not here.
- `type`: `customer` = any external stakeholder present; `internal` = team only. Format (review, workshop, demo) lives in the title and body, not in `type`.
- `who` is the organizer/lead. One person, exact name.
- `attendees` includes `who` plus everyone else. The harness builds person→meeting indexes from this array.
- `project` must match the parent folder name under `projects/`.

## No structured reference fields

Meeting frontmatter has no `from`, `links`, or `retires`. Meetings don't enumerate their outputs — decisions and actions point *to* the meeting, not the reverse. Obsidian backlinks provide free reverse lookup.

## Body

No enforced structure. Conventional sections help readers:

```markdown
## Summary
<1–3 sentences: what the meeting was about and what came out of it>

## Key Discussion Points
- <bullet>

## Decisions
- <summary> [dec-NNN]
- <summary> [dec-NNN]

## Action Items
- <owner>: <task> [act-NNN]
- <owner>: <task> [act-NNN]

## Related
[[requirements/...]]
[[risks/...]]
```

- Decisions and Action Items MUST include bracket IDs inline. Without them, meeting-to-everything trace breaks.
- Wikilinks and bracket IDs can coexist in the same paragraph.
- Narrative discussion content belongs in Key Discussion Points, not crammed into the JSONL `context` field.

## Name validation

Every name in `who` and `attendees` must exist in `team.yaml` (internal) or the project's `contacts.yaml` (external). Unknown names are flagged — not invented. If the PM confirms a new name, the curation flow adds it to contacts.yaml before writing the meeting MD.

## Meetings are events, not state

Meetings are never retired. No `status` field, no `when_resolved`. A meeting happened; it stays in the vault.
