---
description: Answer open-ended questions about vault state by composing deterministic scripts, then narrating the result. Read-only. Use when the PM asks a specific one-off question ("why did we defer X", "who owns the vLLM risk", "show me every decision that retired dec-007") rather than a recurring templated view.
---

# query — open-ended vault question

## When to Use

The PM has a specific question that isn't a recurring briefing. Examples:

- "What's the provenance chain for the FAQ Agent scope decision?"
- "Show me every risk in the configuration category, open or not."
- "Which decisions has dec-042 retired, directly or transitively?"
- "Who's the owner on every open task tagged to the Woori project?"

If the question is recurring and template-shaped, use `brief` instead. If the answer requires filing a new entry, hand off to `curate`.

## Conventions Loaded at Skill Start

**Always:** `conventions/references.md`, `conventions/timestamps.md`.

**Conditionally** — load the convention for whichever entity types the question touches: `conventions/jsonl.md` (decisions/actions questions), `conventions/md-requirements.md`, `conventions/md-risks.md`, `conventions/md-meetings.md`, `conventions/linear-tickets.md` (if ticket IDs appear).

## Workflow

1. **Classify the question.** Which entity types and which scripts? Don't start reading vault files directly — pick the right tool first.

2. **Compose scripts.** Each script is a deterministic one-shot. Chain them:

   | Script | Answers |
   | --- | --- |
   | `active_decisions.py` | What decisions are currently active? |
   | `aging_pending.py` | What's been sitting too long? |
   | `link_graph.py` | What points to / from this entry? |
   | `frontmatter_index.py` | What MDs match a field filter? |
   | `resolve_name.py` | Who is this token? |
   | `validate_jsonl.py` | Is this JSONL schema-clean? |

3. **Walk provenance via `from`.** "Why did we decide X" = `link_graph.py dec-X` → follow the `from` chain backwards (usually meeting wikilink or a raised decision).

4. **Walk retirement via `retires`.** "What did we supersede" = read the entry's `retires` array directly from `decisions.jsonl`.

5. **Use Obsidian backlinks for MD reverse lookups.** A risk MD doesn't list "the decisions that addressed me"; the backlink graph does. When `obsidiantools` is available, prefer it over grep for body-link traversal.

6. **Narrate the answer.** Don't just dump JSON. Frame the answer in prose: "dec-042 was made on {when} by {who}, resolving dec-039 which had been raised in the {meeting}. It retired dec-031 (the earlier limit decision)."

7. **Cite what you looked at.** End with the actual bracket IDs / paths you pulled from, so the PM can verify.

## Gotchas

- **The resolver doesn't answer questions.** Don't mistake `resolver.md` for a query source; it's routing only.
- **Don't rebuild state from decisions.jsonl alone.** Active-decision computation needs set-subtraction by the `retires` field — `active_decisions.py` already does this. Don't reinvent it.
- **Raised vs. made vs. dropped.** "Pending decisions" means `decision-raised` not yet closed by a `from`-pointer. Not "all decision-raised entries" — some are already resolved by later made/dropped entries.
- **Cross-project IDs.** `[prj-NNN:dec-NNN]` means "decision in another project." Don't silently elide the project scope — ask the PM if unsure which project to query.
- **Linear tickets need external resolution.** Query can surface ticket IDs but cannot fetch Linear status. Note the tickets and let the PM (or a Linear MCP) resolve from there.

## Output

Prose answer, grounded in specific bracket IDs and paths. No vault writes.
