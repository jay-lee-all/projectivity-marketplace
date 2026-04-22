# Requirement MD Conventions

Rules for `projects/{project}/requirements/{slug}.md`. Loaded by `curate`, `audit`, and `query`.

## Filename

- Descriptive slug, lowercase, hyphen-separated. Examples: `faq-agent.md`, `document-search-agent.md`, `error-messages-kr.md`, `llm-gateway.md`.
- No `specs/` subfolder. Requirements are flat under `requirements/`.
- The bracket ID resolver scans frontmatter `id`, so the filename can change without breaking `[req-NNN]` references (but prefer stable names anyway).

## Frontmatter (required, 6 fields)

```yaml
---
id: req-NNN
title: <human-readable>
status: active | in-progress | done | deferred | descoped | retired
who: <owner, name from team.yaml or contacts.yaml>
when_created: 2026-02-20T14:30:00
when_completed:                            # empty until status=done
---
```

- `id` is stable. Bracket IDs `[req-NNN]` resolve to this.
- `status`:
  - `active` — defined, not started
  - `in-progress` — work underway
  - `done` — fill `when_completed`
  - `deferred` — paused, may resume
  - `descoped` — removed from scope
  - `retired` — consolidated into or replaced by another requirement; body should wikilink to the replacement
- `when_created` is naive ISO 8601 — KST is implicit, no `+09:00` suffix (see `timestamps.md`).
- `when_completed` is empty unless `status == done`. Presence is the signal — no separate flag.

## Body

Two conventional sections; neither is strictly required for thin requirements.

```markdown
## Spec
<what this requirement is, acceptance criteria, technical constraints, Linear tickets>

## Updates
YYYY-MM-DD — <change> [[meetings/...]] [dec-NNN]
YYYY-MM-DD — <change> [[meetings/...]] [dec-NNN]
```

- `## Spec` holds the substance: functional requirements, UX, API contracts, integration points, Linear ticket references (bare tokens like `FDSE-1509`).
- `## Updates` is a human-readable change log. Each line dates a change and links to the source (meeting and/or decision). Not the authoritative history — that's git — but faster to read.

For a one-line requirement (trivial spec), a single paragraph with no headings is fine.

## Connections live in the body

Frontmatter has no `from`, `links`, or `retires`. Instead:
- Wikilink to meetings in Updates: `[[meetings/2026-02-20-kickoff]]`
- Bracket IDs to decisions/actions: `[dec-010]`, `[act-032]`
- Wikilink to replacement requirements: `Replaced by [[requirements/other-requirement]]`

Obsidian resolves wikilinks natively. The plugin resolves bracket IDs on click. The harness queries connections via the Obsidian link graph (`obsidiantools` backlinks).

## Status transitions

Direct frontmatter edits. Git captures the diff. When a transition has a reason worth preserving (scope creep, customer request, strategic pivot), add a line to `## Updates` linking to the source.

When the transition is also a decision, log a `decisions.jsonl` entry and include the requirement's bracket ID (`[req-NNN]`) in that decision's `links`. Then update the frontmatter `status`. One write per retirement, no dual-write contract.

## Retirement & consolidation

- Set `status: retired`.
- Add to the body: `Replaced by [[requirements/new-requirement]]`.
- The MD frontmatter is the sole source of truth for activity. No JSONL file retires a requirement — `[req-NNN]` never appears in any JSONL `retires` array.

## Validation checklist

- [ ] `id` is unique across this project's `requirements/*.md`.
- [ ] `status` is one of the six legal values.
- [ ] `who` matches `team.yaml` or `contacts.yaml` exactly.
- [ ] `when_created` is naive ISO 8601 (no `+09:00` suffix).
- [ ] `when_completed` is present iff `status == done`.
- [ ] Body wikilinks and bracket IDs resolve.
