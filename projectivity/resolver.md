# Resolver — Routing Table

A traffic cop, not a filing cabinet. This file answers one question: **when skill X fires, which conventions does it need?** Nothing more. The rules themselves live in `conventions/*.md` and get pulled in on demand.

Garry Tan's rule applies: a resolver is pointers, not content. Keep this file short. If you find yourself explaining *what* a convention says here, move the explanation back into the convention file.

## Skill → conventions

Each skill declares its convention set via frontmatter `hooks` (skill-start inject). This table is the authoritative mapping; if a skill's frontmatter drifts from this table, fix the skill, not the table.

| Skill | Sector | Always loads | Conditionally loads |
| --- | --- | --- | --- |
| `meeting` | Curation (precursor) | `md-meetings.md`, `timestamps.md`, `references.md` | — |
| `curate` | Curation | `filing-triggers.md`, `jsonl.md`, `references.md`, `timestamps.md`, `linear-tickets.md` | `md-meetings.md` (if producing/updating a meeting), `md-requirements.md` (if touching requirements), `md-risks.md` (if surfacing/updating a risk) |
| `brief` | Execution (read-only) | `references.md`, `timestamps.md` | `linear-tickets.md` (if template pulls Linear data) |
| `query` | Execution (read-only) | `references.md`, `timestamps.md` | `jsonl.md` (questions over decisions/actions), `md-requirements.md` / `md-risks.md` / `md-meetings.md` (per entity type the question touches), `linear-tickets.md` (if ticket IDs appear) |
| `audit` | Utility (read-only) | `jsonl.md`, `references.md`, `timestamps.md`, `linear-tickets.md`, `md-meetings.md`, `md-requirements.md`, `md-risks.md` | — (audit inspects everything) |
| `scaffold` | Utility | `references.md`, `timestamps.md` | `md-requirements.md` (new requirement), `md-risks.md` (new risk), `md-meetings.md` (new meeting scaffolds), `jsonl.md` (if pre-seeding JSONL schema headers) |

`filing-triggers.md` is **curate-only** — it's judgment guidance for "does this become a decision, an action, or a risk?" Other skills don't need it because they don't file; they read what's already filed.

## Intent → conventions (when no skill fires)

Used by ad-hoc invocations where Claude is editing the vault without going through a skill (direct user request, debugging, scaffold follow-ups).

| Intent | Load |
| --- | --- |
| Writing to `decisions.jsonl` or `actions.jsonl` | `jsonl.md` + `references.md` + `timestamps.md` (mandatory — no exceptions) |
| Editing a meeting MD | `md-meetings.md` + `references.md` + `timestamps.md` |
| Editing a requirement MD | `md-requirements.md` + `references.md` + `timestamps.md` |
| Editing a risk MD | `md-risks.md` + `references.md` + `timestamps.md` |
| Resolving a Linear ticket reference | `linear-tickets.md` |
| Deciding "is this a decision or an action?" | `filing-triggers.md` |
| Deciding "is this a risk or a decision-raised?" | `filing-triggers.md` + `md-risks.md` |
| Adding a new category or type value | check the relevant convention's working-set guidance first; propose, don't force-fit |

## File type → conventions (fallback)

If intent is unclear and only the file path is known, load by extension.

| Path pattern | Load |
| --- | --- |
| `**/*.jsonl` | `jsonl.md` + `references.md` + `timestamps.md` |
| `**/meetings/*.md` | `md-meetings.md` + `references.md` + `timestamps.md` |
| `**/requirements/*.md` | `md-requirements.md` + `references.md` + `timestamps.md` |
| `**/risks/*.md` | `md-risks.md` + `references.md` + `timestamps.md` |
| `**/timeline.yaml` | `timestamps.md` + `references.md` (for `ms-NNN` / `dl-NNN` usage notes) |
| `**/team.yaml`, `**/contacts.yaml` | `references.md` (name resolution) |

## What the resolver does NOT do

- **It is not a schema.** Don't read this file expecting to learn what fields a decision entry has — read `conventions/jsonl.md`.
- **It is not a skill index.** Skill authoring (frontmatter, workflow, confirmation steps) lives in each `skills/{name}/SKILL.md`.
- **It does not enumerate scripts.** Script descriptions live in their own source files and in the skills that invoke them.
- **It does not resolve references.** `[dec-NNN]` / `[[path]]` resolution is a harness/plugin concern (Obsidian + bracket-ID resolver), not a routing concern.

## Validation (for plugin maintainers)

Each entry in the Skill → conventions table must satisfy:

- [ ] The skill directory `skills/{name}/` exists.
- [ ] Every convention file referenced exists in `conventions/`.
- [ ] The skill's `SKILL.md` frontmatter `hooks` list matches the "always loads" column for that skill.
- [ ] No convention is referenced here that isn't in `conventions/` (Garry's `check-resolvable` problem).

Run this check before cutting a plugin release.
