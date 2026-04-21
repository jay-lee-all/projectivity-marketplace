---
description: Answer open-ended, one-off questions about vault state by composing deterministic scripts and narrating the result. Use for ad-hoc PM questions: "why did we defer X", "who owns the vLLM risk", "show every decision that retired dec-007", "what's the provenance chain on dec-042". Read-only. For recurring template-shaped views use `brief`; if the answer needs to be filed, hand off to `curate`.
hooks:
  - conventions/references.md
  - conventions/timestamps.md
---

# query — open-ended vault question

## When to Use

The PM has a specific question that isn't a recurring briefing. Examples:

- "What's the provenance chain for the FAQ Agent scope decision?"
- "Show me every risk in the configuration category, open or not."
- "Which decisions has dec-042 retired, directly or transitively?"
- "Who's the owner on every open task tagged to the Woori project?"

If the question is recurring and template-shaped, use `brief` instead. If the answer requires filing a new entry, hand off to `curate`.

## Conventions

Frontmatter `hooks` declares the always-load set (`references.md`, `timestamps.md`). Conditionally load the convention for whichever entity types the question touches:

- `conventions/jsonl.md` — decisions or actions questions.
- `conventions/md-requirements.md`, `conventions/md-risks.md`, `conventions/md-meetings.md` — per entity type.
- `conventions/linear-tickets.md` — if Linear ticket IDs appear.

## Workflow

1. **Classify the question.** Which entity types and which scripts? Don't start reading vault files directly — pick the right tool first.

2. **Compose scripts.** Each script is a deterministic one-shot. Chain them:

   | Script | Answers |
   | --- | --- |
   | `active_decisions.py --project X [--since YYYY-MM-DD]` | What decisions are currently active (made-type, not retired)? |
   | `aging_pending.py --project X --threshold N [--include-tasks]` | What raised decisions / open tasks have been sitting too long? |
   | `link_graph.py <id> --project X` | What points to / from this entry (1-hop)? |
   | `frontmatter_index.py <folder> [--filter k=v]` | What MDs match a field filter? |
   | `meeting_context.py --project X [--attendees ...]` | What's the prior-meeting context for attendees on a project? |
   | `resolve_name.py <token> [--team team.yaml]` | Who is this token (Slack id / email / name)? |
   | `validate_jsonl.py <path>` | Is this JSONL schema-clean? |

   Scripts never write. If a question requires writing, hand off to `curate`.

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
- **Vault location.** Scripts resolve the project via `$PROJECTIVITY_VAULT` or `cwd/Project_OS`. If they fail with "project directory not found", use `--path "<absolute>/projects/<slug>"` as a fallback.

## Verification

Open-ended answers are easy to fudge with confident-sounding prose. Before delivering:

1. **Every claim is tied to a script call.** If the answer says "dec-042 retires three earlier decisions", the `retires` array in the entry should literally have three elements. No claim should rest on inference Claude made between script calls without re-checking.
2. **IDs in the prose appear in the tool output.** Cross-check the bracket IDs you cited against the JSON your scripts returned. Hallucinated IDs are the most common failure mode here.
3. **Provenance chains terminate.** If you walked `from` chains, the chain ends at a meeting MD or a "no `from`" entry — not mid-walk because you got bored. State explicitly where the chain stops.

## Output

Prose answer, grounded in specific bracket IDs and paths the PM can grep for. End with a "Cited entries" list. No vault writes.
