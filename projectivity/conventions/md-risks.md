# Risk MD Conventions

Rules for `projects/{project}/risks/{slug}.md`. Loaded by `curate`, `audit`, and `query`.

## Filename

- Descriptive slug, no date prefix. The risk's identity is the problem, not the date. Examples: `pii-timeout-cascade.md`, `vllm-token-overflow.md`, `qwen3-tokenizer-mismatch.md`, `vendor-ssl-renewal.md`.
- The date lives in `when_surfaced` frontmatter. `id` (`risk-NNN`) handles bracket ID resolution.

## Frontmatter (required, 6 fields)

```yaml
---
id: risk-NNN
title: <human-readable>
when_surfaced: 2026-03-18T13:00:00+09:00
when_resolved:                    # empty while open
who: <owner, name from team.yaml>
category: infrastructure | model | integration | configuration | customer | process
---
```

- `when_surfaced` and `when_resolved` are ISO 8601 with KST. `when_resolved` empty ⇒ open.
- `category` is the working set — an open vocabulary, not a closed enum. If a real risk genuinely doesn't fit one of these, the curation flow can propose a new category for the PM to confirm; don't force a bad fit. Additions become proposed updates to this file.

## Body

Continuous write-up, starts thin, grows. No mandatory structure.

```markdown
<opening line: what the risk is, when surfaced, where it came from>
발견 경위: [[meetings/...]]

## Investigation
<root cause analysis, rejected hypotheses, engineering hours, affected systems>

## Resolution
<what was done>
관련 결정: [dec-NNN]
구현: [act-NNN]
Linear: FDSE-NNNN
```

For a thin risk (known blocker, obvious fix), a paragraph is enough. For a complex one, the body accumulates investigation and resolution over days or weeks.

## Temporary mitigations are first-class risks

When an engineer applies a quick fix — raising a config limit, disabling a component, falling back to a manual process — **open a risk MD**. Don't skip because it feels ephemeral; "temporary" changes become invisible permanent drift.

Shape:
- `category: configuration` (or similar)
- Body describes: original state, new state, rationale, **conditions for reversion or formalization**.
- Risk stays open until either a `decision-made` formalizes the change (fill `when_resolved`, add Resolution section pointing to the decision) or an action reverts it.

Trigger phrases to watch for in curation: `일단 ~로 임시 상향`, `임시로 ~ 비활성화`, `workaround`, `hotfix`, `revert later`.

## Connections live in the body

Frontmatter has no structured reference fields. Instead:
- Wikilinks to the meeting that surfaced or discussed it: `[[meetings/2026-03-18-infra-review]]`
- Bracket IDs to the driving decision and implementation action: `[dec-012]`, `[act-032]`
- Wikilinks to threatened requirements: `[[requirements/faq-agent]]`
- Wikilinks to related risks, including absorption: `[[risks/vllm-config-drift]]`

Obsidian backlinks surface reverse connections automatically.

## Lifecycle

- **Surface:** create file, frontmatter + opening line, leave `when_resolved` empty.
- **Investigate:** edit body over time; add findings, rejected hypotheses, links.
- **Resolve:** fill `when_resolved`, add `## Resolution` section, link to driving decision and implementation action.
- **Absorb** (broader risk supersedes this one): fill `when_resolved`, add `Absorbed by [[risks/broader-risk]]` line in the body.
- **Reopen:** clear `when_resolved` and add a new section describing the recurrence; or create a new risk file wikilinking back — curation asks the PM.

## Retirement lives in frontmatter

Frontmatter `when_resolved` is the sole source of truth for whether a risk is open. No JSONL file retires a risk — `[risk-NNN]` never appears in any JSONL `retires` array. When a decision resolves a risk, record the connection via the decision's `links`, then fill `when_resolved` directly.

## Validation checklist

- [ ] `id` is unique across this project's `risks/*.md`.
- [ ] `when_surfaced` has KST offset.
- [ ] `when_resolved` is either empty or a KST ISO 8601 string.
- [ ] `who` matches `team.yaml` or `contacts.yaml`.
- [ ] `category` is from the working set (or PM-confirmed addition).
- [ ] Temporary mitigation risks name the reversion/formalization conditions in the body.
