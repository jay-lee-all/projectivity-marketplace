# Reference System

The vault uses two reference formats plus three structured fields (JSONL only). This file is the definitive runtime summary.

## Two formats

### Wikilinks — `[[path]]`

For referencing **files**: MD, YAML, or any file with a path.

```
[[meetings/2026-02-20-kickoff]]
[[requirements/faq-agent]]
[[risks/pii-timeout-cascade]]
[[core/contacts.yaml]]
```

Obsidian resolves natively — clickable, visible in graph view, creates backlinks. Cross-project wikilinks use relative paths: `[[../other-project/risks/vllm-config-drift]]`.

### Bracket IDs — `[prefix-NNN]`

For referencing **entries by ID**. Two kinds of targets:

- **JSONL entries** — `[dec-001]`, `[act-005]` — resolve to a line in `decisions.jsonl` / `actions.jsonl`.
- **MD entities** — `[req-001]`, `[meet-003]`, `[risk-001]` — resolve to an MD file whose frontmatter `id` matches. File path is not encoded; the resolver scans frontmatter to find the match. This makes bracket IDs rename-proof.

Prefixes handled by the plugin/resolver:

| Prefix | Target |
| --- | --- |
| `dec-` | decisions.jsonl entry |
| `act-` | actions.jsonl entry |
| `req-` | requirements/*.md |
| `meet-` | meetings/*.md |
| `risk-` | risks/*.md |

Normal bracket usage like `[see above]` is untouched — only the five known prefixes resolve.

Cross-project bracket IDs use `[prj-NNN:prefix-NNN]`:

```
[prj-002:dec-001]
```

The harness splits on `:` — left side is a project ID, right side is the entry ID within that project.

### Timeline IDs are NOT bracket IDs

`dl-NNN` (deadlines) and `ms-NNN` (milestones) live only in `timeline.yaml` and in free-text mentions inside action `what` fields (e.g. `"ms-001 shifted 5/15→5/22"`). They are **not wrapped in brackets** and **not resolved by the plugin**. A PM reads timeline.yaml as a single short file; clickable cross-references don't earn their keep at that scale.

### Linear tickets are NOT bracket IDs

Linear ticket IDs (e.g. `FDSE-1509`, `AI-1487`) are **bare tokens**, never written as `[FDSE-1509]`. See `linear-tickets.md` for the full convention.

## Three structured fields (JSONL only)

`decisions.jsonl` and `actions.jsonl` share these three fields. Each answers a distinct question. No overlap.

### `from` — Why does this entry exist?

Single value (not an array). Wikilink or bracket ID. Optional in most cases; **required on `decision-dropped`** (must point to the `[dec-NNN]` raised entry being dropped).

Forms:
- A decision made in a meeting: `"from": "[[meetings/2026-02-20-kickoff]]"`.
- A decision-made resolving a prior raised question: `"from": "[dec-007]"`.
- A task-done completing its task-created: `"from": "[act-001]"`.
- A task-blocked pointing at the blocked task: `"from": "[act-002]"`.

Omit when there's no clear single origin (e.g. a spontaneous `note`).

### `links` — What else is relevant?

Array, mixed wikilinks and bracket IDs. Omit entirely when empty (not `[]`).

Examples:
```json
"links": ["[[requirements/faq-agent]]", "[dec-001]", "FDSE-1509"]
```

What belongs:
- Related specs, related decisions, related actions
- Context files, threatened requirements, addressed risks
- Cross-project references
- Linear ticket IDs (as bare tokens — see linear-tickets.md)

What does NOT belong:
- The origin (use `from`)
- Entries this makes obsolete (use `retires`)

### `retires` — What does this make inactive?

Array of same-schema bracket IDs. Optional; omit when this entry doesn't deactivate anything.

Strict rules:
- `decisions.jsonl`: `retires` is only valid on `decision-made`, and can only target other `decision-made` IDs. Raised entries close via `from`; dropped entries are already terminal.
- `actions.jsonl`: `retires` targets `[act-NNN]` IDs only.
- **Never** target MD entities: `[req-NNN]`, `[meet-NNN]`, `[risk-NNN]` must never appear in any JSONL `retires`. MD entities retire through their own frontmatter.

## MD entities don't use these fields

Meetings, requirements, and risks have **no structured reference fields** in frontmatter. Their connections live in the body as wikilinks and bracket IDs, queryable via the Obsidian link graph (`obsidiantools` backlinks).

Retirement:
- Requirements: frontmatter `status` → `retired` / `descoped` / `deferred`.
- Risks: frontmatter `when_resolved` filled.
- Meetings: never retired — they're events.

When a decision drives the retirement, record the connection in that decision's `links` array. The MD's body (Updates section for requirements, continuous body for risks) may also link back to the decision. Obsidian backlinks surface the reverse automatically.

## Reference direction principle

Events reference their origins. Origins do not enumerate their outputs.

- Decisions point to the meeting where they were made (`from`). Meetings do not list their decisions.
- Actions point to their triggering meeting or decision (`from`). Meetings and decisions do not list the actions they produce.
- Requirements and risks link backward via body wikilinks. Obsidian backlinks handle reverse lookup for free.

Why: prevents duplication, keeps JSONL append-only clean, and makes reverse lookups trivial via `grep` (JSONL) or backlinks (MD).

## Quick-reference card

```
[[path]]                  → file (Obsidian resolves)
[prefix-NNN]              → JSONL entry or MD entity (plugin/harness resolves)
[prj-NNN:prefix-NNN]      → cross-project entity
FDSE-NNNN / AI-NNNN / ... → Linear ticket (bare token, see linear-tickets.md)
dl-NNN, ms-NNN            → timeline.yaml internal IDs (no brackets, not resolved)

Known bracket prefixes: dec- act- meet- req- risk-

JSONL reference fields: from (one origin), links (array, mixed), retires (array, same-schema only)
MD frontmatter: no reference fields; body wikilinks + bracket IDs
Direction: events point to origins, not vice versa
```
