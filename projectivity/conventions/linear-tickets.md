# Linear Ticket References

Linear is the engineering ticket system. Ticket IDs appear across Slack threads, meeting notes, and decision context. The vault captures them, but **not as bracket IDs**.

## Format

`{TEAM_PREFIX}-NNNN`, verbatim as written in Linear. Examples:

```
FDSE-1509
AI-1487
ALL-1023
```

Uppercase prefix (2–5 letters), dash, 3–5 digits. Per-team, not company-wide. Each team owns its own Linear project with its own prefix.

## Where prefixes come from

`team.yaml` under `teams[].ticket_prefix`. The harness reads team.yaml at startup, builds the set of valid prefixes, and recognizes tokens of shape `{PREFIX}-\d{3,5}` in free text only when `{PREFIX}` is in that set. Unknown prefixes (e.g. `FOO-1234` where `FOO` isn't a ticket_prefix) are treated as normal text — not misidentified as tickets.

## How to write them

**Inline in text fields** (`decision`, `question`, `context`, `what`, meeting/requirement/risk body):

```
"context": "FDSE-1509 한도 300개 임시 상향 유지 중. 플랫폼팀 성능 부담 우려."
```

Bare token, inline with the prose. No brackets.

**In `links` arrays** (when the ticket is a primary related resource):

```json
"links": ["[[requirements/limit-config]]", "FDSE-1509"]
```

Bare token as a string element. **Never** wrap in single brackets — `[FDSE-1509]` is malformed. Bracket IDs are reserved for vault-internal entries (`dec-`, `act-`, `req-`, `meet-`, `risk-`).

## Why not bracket IDs

Bracket IDs resolve to entries *inside the vault* (a JSONL line or an MD frontmatter match). Linear tickets resolve to URLs *outside* the vault (`https://linear.app/{workspace}/issue/{prefix}-{n}`). The resolution target is categorically different. Keeping them as plain tokens:

- Avoids pretending they're the same kind of reference.
- Keeps them greppable and LLM-parseable.
- Lets a Linear-specific plugin or URL template make them clickable without conflicting with the vault's bracket ID resolver.

## Validation

- [ ] No Linear ticket is wrapped in single brackets.
- [ ] Prefix is uppercase and present in `team.yaml`.
- [ ] Digits are 3–5 long.

## Curation note

When curating from Slack or Linear dumps, extract ticket IDs found in the source text and place them:
- Inline in the relevant `context` / `what` / body text (for narrative).
- In `links` as bare tokens (when the ticket is the primary external reference).

Don't invent ticket IDs. If a Slack thread references a ticket without giving the ID, leave the reference descriptive (e.g. `"FDSE 관련 티켓"`) and let the PM fill it in during confirmation.
