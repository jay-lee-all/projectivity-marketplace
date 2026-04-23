# Filing Triggers — When to Create What

Judgment guidance for curation. When a source (meeting, Slack thread, Linear ticket, email) surfaces new information, this file tells Claude which entity type to create, and why. Loaded by `curate`.

## The core question

> Does this constrain future choices — or would it, if answered?

If yes, it's a **decision** (raised or made). If no, it might be an action, a note, or a risk — use the rules below.

## Decision — raised

A question or proposal was surfaced that will constrain future choices **once answered**. Not yet committed.

Triggers:
- "We need to decide whether to X or Y."
- "Customer is asking for Z — we haven't answered yet."
- "Should we use approach A or approach B?"
- Multiple options are live; no commitment has been made.

Shape: `type: decision-raised`, `question` field (not `decision`), `from` usually the meeting wikilink.

## Decision — made

The project committed to an answer. Most decisions land here directly without a prior raised entry — that's normal and desired.

Triggers:
- "We decided to X."
- "Going with Y."
- "Confirmed A."
- A definitive commitment that will constrain future choices.

Shape: `type: decision-made`, `decision` field, `context` for the why. If it resolves a prior raised question, `from` points to that `[dec-NNN]`; otherwise `from` is the meeting wikilink (or omitted for informal commitments).

## Decision — dropped

A previously raised question is closed **without** a commitment — overtaken by events, deferred indefinitely, answered elsewhere, or the customer withdrew the ask.

Triggers:
- "Customer withdrew the request."
- "Rolled into [bigger decision]."
- "Not relevant anymore."
- "Deferred to phase 2 indefinitely."

Shape: `type: decision-dropped`, `from` **required** and pointing to the raised entry being dropped, `context` carries the closure reason. `decision` field optional as a short label ("음성 Agent 우선순위 검토 건").

## Action — task-created

A task the **project** needs to track at the PM layer — regardless of who owns it. Engineering work that lives fully inside Linear stays there; what comes here are the project-visible events: an engineer completing a deployment push, a customer requesting infrastructure changes, a PM scheduling a follow-up, a cross-team coordination ask. The test: **"is this a project event, or is it an individual's ticket?"**

Triggers:
- "Jay will send the requirements doc."
- "Engineer is driving the overnight prod stabilization push."
- "Customer DevOps is requesting MFA account provisioning."
- "Schedule the follow-up meeting."
- "Review the competitor demo."
- "Follow up with 김철수 next week."

## Action — task-done, task-blocked

- `task-done`: task completed. `from` → the `task-created` entry.
- `task-blocked`: task can't proceed; describe the blocker in `what`. `from` → the blocked task.

## Action — communication

A significant communication event worth finding 3 months from now. Communications are the noisiest type — apply **both** tests before filing:

1. **Would I need to find this 3 months from now?**
2. **Does this carry information not already captured by a decision, action, or risk in this plan?** If the answer is already filed as `[dec-NNN]`, don't also file a communication saying "someone asked about it." The decision is the record; the Slack thread is the color.

Signal (file these):
- Engineer sharing a deployment completion report with the customer.
- Customer infrastructure team requesting a security architecture diagram.
- Customer DevOps requesting MFA account provisioning.
- PM sharing document-management guidelines post-incident.

Noise (skip):
- Engineer asking a teammate how to use a tool (support, not project event).
- "Sounds good" / "thanks" acknowledgments.
- Dashboard link requests (operational, not strategic).
- Internal pings asking "is X confirmed?" when X is already filed as a decision.

**Customer acceptance / feedback is always signal.** When a customer confirms a deliverable meets requirements, rejects it, or gives substantive quality feedback, always file it — these are among the hardest events to reconstruct later and the most valuable for retrospectives and future scoping. Examples: "customer tested RAG agent on 50 queries, accuracy acceptable for pilot"; "customer rejected OCR quality, requested re-processing."

## Action — milestone

A project milestone reached. **Must be paired with a `timeline.yaml` update in the same curate plan** — move the milestone from `milestones:` to `done:` with a `completed:` date. Curate's write-order handles this; don't file a `milestone` action without the yaml move, or the two halves drift.

Triggers:
- "MVP deployed to staging."
- "Customer UAT sign-off received."
- "Requirements frozen."

## Action — milestone-shifted

A milestone's target date moved significantly, with a reason worth preserving. **Don't log trivial date tweaks** (holiday shift, a few days with no reason) — those are direct edits to timeline.yaml.

Trigger: scope change, blocker, customer request, risk materialized → log with old date, new date, reason in `what`.

## Action — note

High-value context that doesn't fit anywhere else.

Triggers:
- Customer sentiment ("budget concern mentioned in passing").
- Political dynamics.
- Process observations ("noticed latency spike but customer didn't comment").
- Something worth surfacing in later workflows.

These are **not throwaway entries** — the harness surfaces them in relevant briefings.

## Risk MD

A systemic threat to project delivery — technical failure, cascade failure, operational gap, model behavior regression, customer-side blocker, configuration drift.

Triggers:
- "vLLM service can lock the PII pipeline." — infrastructure risk.
- "Token overflow on Qwen3 with long context." — model risk.
- "SSL cert renewal not confirmed." — configuration risk.
- "Customer legal team hasn't reviewed." — customer risk.

## Risk MD — temporary mitigation (critical)

A quick fix was applied that isn't the final answer. **Open a risk MD.** Do not skip because it feels ephemeral — "temporary" becomes invisible permanent drift.

Trigger phrases (Korean and English):
- `일단 ~로 임시 상향`
- `임시로 ~ 비활성화`
- `workaround`
- `hotfix`
- `revert later`
- `until we figure out a proper fix`

Shape: category `configuration` (or similar), body includes:
- What the original state was.
- What the new state is.
- The rationale for the change.
- **Conditions for reversion or formalization** — the path to closing the risk.

Risk stays open until a `decision-made` formalizes the change (then `when_resolved` + Resolution section) or an action reverts it.

## Requirement MD

A deliverable with a lifecycle (active → in-progress → done, sometimes deferred/descoped/retired) and substance (what it is, acceptance criteria, Linear tickets).

Triggers:
- Customer asks for a new capability.
- Scope discussion surfaces a new deliverable worth tracking.
- Existing requirement splits into multiple.

Don't create requirements for engineering tickets — those are in Linear. A requirement is the PM-layer "what are we delivering." Linear tickets link to it via bare tokens in the body.

## Meeting MD

Any customer or internal meeting with project-relevant content. Produced by the `meeting` skill from a transcript or notes; curation then operates on that meeting MD plus any other sources.

Don't create meeting MDs for routine standups unless something project-relevant came out of them (a decision, an action, a risk).

## Decision vs. action — the fast test

If the same question could be asked differently in 3 months and change the project direction → **decision**. If it's just a thing that needs doing, with no branching future → **action**.

Bad boundary cases:
- "Move standup to Thursday" — action (no future constraint).
- "Use Claude over GPT-4o for the FAQ Agent" — decision (constrains LLM choice going forward).
- "Review the competitor demo" — action (one-off).
- "Standardize on OpenAI for all LLM work" — decision (constrains every future LLM choice).

## Default: log it, let audit filter

When unsure, log it. The `audit` skill surfaces thin/low-quality entries for review. Missing information is worse than over-recording — every other failure mode is recoverable, but a missed decision is invisible by definition.

## Multi-entity cases

One source often produces multiple entities. A meeting might yield: 1 meeting MD, 2 decisions, 3 actions, 1 risk, 1 requirement update. The `curate` skill is unified exactly to handle this — it builds the full plan before any write, writes in dependency order (meeting → decisions → actions → requirements → risks), and presents everything for PM confirmation as one unit.

Ordering matters because cross-references depend on it — an action's `links` pointing to a decision needs the decision's ID to exist first.
