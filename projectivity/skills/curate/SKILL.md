---
description: Unified curation pass that turns a source (meeting MD, Slack thread, Linear dump, email, manual notes) into vault entries — decisions, actions, requirement updates, risks — in one consistent pass. Use after `meeting`, or any time a source has new signal: "file this thread", "log what came out of the call", "add a risk for the temporary rate-limit". One confirmation plan; nothing written until PM approves.
hooks:
  - conventions/filing-triggers.md
  - conventions/jsonl.md
  - conventions/references.md
  - conventions/timestamps.md
  - conventions/linear-tickets.md
  - conventions/curate-state.md
---

# curate — source → vault entries

## When to Use

A source has new signal that should land in the vault: a just-written meeting MD, a Slack thread the PM pasted in, a Linear export, an email chain. One source typically produces multiple entity types (decisions + actions + risks); this skill handles all of them in one pass so cross-references are consistent.

Do **not** use this skill to:

- Create a meeting MD from a transcript — that's `meeting`.
- Edit an existing requirement or risk outside the context of a source — read and edit directly.
- Scaffold new structure — that's `scaffold`.

## Conventions

Frontmatter `hooks` declares the always-load set the resolver injects at skill start: `filing-triggers.md`, `jsonl.md`, `references.md`, `timestamps.md`, `linear-tickets.md`, `curate-state.md`.

**Conditionally load** when the plan touches an entity type:

- `conventions/md-meetings.md` — if producing or updating a meeting MD.
- `conventions/md-requirements.md` — if touching requirements.
- `conventions/md-risks.md` — if surfacing or updating a risk.

The conventions are authoritative; do not restate their contents here.

## Workflow

1. **Load project state.** Read `projects/<slug>/core/curate-state.yaml`. The per-source `last_..._ts` values are the implicit lower bounds for this run; `now()` is the upper bound. `--since <date>` / `--until <date>` CLI overrides replace these. **Inline sources bypass the state file** — if the PM pastes a Slack thread or names a meeting MD directly, that source is ingested as-given without consulting the state file's timestamp for it (but other sources still respect their state). See `conventions/curate-state.md` for the contract.

2. **Read the source fully before filing anything.** Sources are often multi-threaded; a decision on line 40 may be dropped on line 80.

3. **Plan first, write second.** Build a full plan covering every proposed entity before writing any file. Ordering matters — cross-references depend on IDs existing.

   Follow the shape in [templates/proposal-preview.md](templates/proposal-preview.md). That's the format the PM sees at confirmation — keep sections in the same order so the review is predictable.

   Three plan-stage checks that are easy to miss:
   - **Every `task-done` / `task-blocked` has a `task-created` upstream.** If not: reclassify (likely a `communication` or `note`) or file the missing `task-created` retroactively in this plan. `validate_jsonl.py` will warn post-write, but catching it in the plan is cheaper.
   - **No `task-created` gets two closures.** Two completions pointing at the same origin → split the original task into distinct `task-created`s.
   - **Every `task-created` spawned by a decision carries that decision's bracket ID in `links`.** `jsonl.md` calls this "the weak link"; the plan review is the enforcement point — the source rarely spells the connection out.

4. **Use filing-triggers guidance.** The "is this a decision or an action?" call is in `filing-triggers.md`; consult it. When uncertain, log it — audit filters noise later.

5. **Watch for temporary-mitigation language.** Trigger phrases: `일단 ~로 임시 상향`, `임시로 ~ 비활성화`, `workaround`, `hotfix`, `revert later`, `until we figure out a proper fix`. Any of these → open a risk MD with `category: configuration` and name the reversion conditions in the body. Do **not** skip because it feels ephemeral — the convention is explicit about this.

6. **Assign IDs in order.** For each JSONL-backed entry, get the next ID first:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --jsonl "projects/<slug>/core/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --jsonl "projects/<slug>/core/actions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --folder "projects/<slug>/risks" --prefix risk-
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" --folder "projects/<slug>/requirements" --prefix req-
   ```

   Allocate sequentially within the plan so `[dec-042]` pointing at `[dec-041]` is consistent before any file is written.

7. **Resolve people.** Any `who`/`attendees`/Slack-ID token goes through `resolve_name.py`. Unresolved tokens are surfaced to the PM during confirmation, never silently filed as raw IDs.

8. **Validate JSONL lines before presenting them.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" \
     --line '<proposed-json-line>' --kind decisions
   ```

   Fix any errors before the confirmation step.

9. **PM confirmation — mandatory, unified.** Present the full plan (meeting, decisions, actions, requirements, risks) in one block. The PM can accept, reject, or edit any part. Write only after approval.

10. **Write in dependency order:** meeting MD (if any) → decisions → actions → **`timeline.yaml` updates (for any `milestone` / `milestone-shifted` action in the plan)** → requirement updates → risk MDs. Cross-references resolve cleanly because dependencies exist first.

11. **Update `core/curate-state.yaml`.** Use `update_curate_state.py` — don't hand-edit the file. For each source this run consumed any items from, pass the latest timestamp consumed; sources not mentioned stay untouched:

    ```bash
    python "$CLAUDE_PLUGIN_DIR/scripts/update_curate_state.py" \
      --project <slug> --mode incremental \
      --source slack_internal=<latest-ts> \
      --source linear=<latest-updated-at>
    ```

    Mode is `incremental` here; backfill's Phase 5 uses `--mode backfill`. Skipping this step means the next curate run will re-read and re-file things already in the vault. See `conventions/curate-state.md` for the full contract and the source-name → field-name mapping.

12. **Post-write summary:** list every file touched with its path, note whether `curate-state.yaml` was updated, and surface any `unresolved` tokens or uncertain filings for the PM to follow up on.

## Backfill Mode

Invoked as `/projectivity:curate --backfill <slug>`. Used when a project has existing history (Slack threads, Linear issues) that was never filed — typically right after `scaffold` on a live project. Overrides: `--since <date>`, `--until <date>`. The normal 12-step workflow above still applies; this section describes the orchestration that runs *around* it, producing one unified plan that the PM approves once.

Backfill is the **first use of subagent orchestration in this plugin.** The pattern documented here is expected to be reused wherever we hit a source volume that would overflow a single agent's context.

**Phase 1 — Probe + scope.** Read `overview.md` for sources (internal Slack, external Slack, Linear project). For each source, probe for earliest relevant data via the Slack/Linear MCP tools: oldest message in each channel, earliest issue update in the Linear project. **Floor the probe at `overview.md:when_created`** — a Slack channel that existed for two years before the project has two years of noise that isn't this project's concern.

Estimate volume (rough count of messages + tickets × a per-item effort guess — e.g. ~0.5 sec/item for judgment + ~1 sec for name resolution). Present to the PM via `AskUserQuestion`:

> Found ~N messages and ~M tickets since `<probe_floor>` (`<weeks>` weeks). Estimated ~`<min>` min to plan. How far back?
> - Full range (from `<probe_floor>`) — recommended
> - Last 2 weeks only
> - Custom date

Default is full. The PM's choice becomes the effective `--since` for this run.

**Phase 2 — Adaptive windowing.** Window size scales with the chosen range, not the content density. The principle: window size should roughly match the cadence at which the PM thinks about the project.

Don't pick the window size by hand — call `backfill_probe.py` with the timestamps you fetched in Phase 1 and the PM's chosen since. It applies the table below and returns the chronological, non-overlapping window list:

```bash
python "$CLAUDE_PLUGIN_DIR/scripts/backfill_probe.py" \
  --project <slug> \
  --slack-earliest <earliest-per-channel> \
  --linear-earliest <earliest-linear-updated> \
  --chosen-since <pm-picked-since>
```

The script floors at `overview.md:when_created`, computes `effective_since/until`, and emits each window as `{index, since, until}`. Reference table (what the script encodes):

| Total range | Window size |
|---|---|
| < ~2 hours | 1 pass, no windowing (runs as a single subagent or inline) |
| < 1 day | hourly, or 1 pass if sparse |
| 1 day – 1 week | daily |
| 1 week – 2 months | weekly |
| > 2 months | weekly or biweekly, aim for 10–15 windows total |

Windows are chronological and non-overlapping.

**Phase 3 — Sequential subagent execution.** For each window in chronological order, the coordinator (the main curate agent) does the following:

1. **Allocate IDs for this window.** Coordinator tracks the next available ID for each type as an in-memory counter. On the first window, it seeds the counters from `next_id.py` run on disk. On subsequent windows, it bumps from the counter's current value — no disk read needed because nothing is written yet.

2. **Spawn an Explore subagent** with exactly these inputs:
   - The window's source slice: date range + which sources (channel IDs, Linear project name).
   - The allocated ID starting points: "your decisions start at `dec-051`, actions at `act-094`, risks at `risk-003`."
   - A **still-open items summary** — id + 1-line per `decision-raised` or `task-created` proposed in *prior* windows that hasn't yet been resolved. Cap it there. Closed items from prior windows and pre-backfill vault entries are NOT passed in — the subagent reads those itself when needed.

3. **Subagent reads the window's sources** via Slack/Linear MCP tools, applies `filing-triggers.md` + `jsonl.md` + MD conventions, and returns structured proposals (in `proposal-preview.md` format) using real IDs from its allocated range. For any **pre-backfill** cross-reference (a Slack message referring to a decision made months ago), the subagent reads the vault directly — `Read` on `core/decisions.jsonl`, `link_graph.py`, grep of `risks/*.md` — and uses the real bracket IDs it finds.

4. **Subagent flags low-confidence items** alongside its proposals: ambiguous filings ("decision or risk?"), unresolved name tokens, temporary-mitigation language it wasn't sure how to categorize. Returned as a separate structured list, not inline in the proposals.

5. **Coordinator merges the window's proposals** into a running plan, bumps in-memory ID counters, and updates the still-open items summary: add newly-proposed unresolved entries; remove entries whose closing event this window produced.

**Phase 4 — Unified plan + single PM approval.** After all windows complete, coordinator assembles one plan in `proposal-preview.md` format. The plan includes a `## Low-confidence items` section at the top, aggregating flags from every subagent — PMs skim there first; the rest of the plan is "trust and approve." Run the normal pre-write validation (`validate_jsonl.py --line` on every proposed JSONL entry) before presenting.

PM approves, edits, or rejects. No writes happen until one approval covers everything.

**Phase 5 — Write, then update state.** Write in the same dependency order as normal curate: meeting MDs → decisions → actions → `timeline.yaml` updates → requirement updates → risk MDs. After successful write, call `update_curate_state.py` with `--mode backfill` and the latest timestamp consumed from each source:

```bash
python "$CLAUDE_PLUGIN_DIR/scripts/update_curate_state.py" \
  --project <slug> --mode backfill \
  --source slack_internal=<latest-ts> \
  --source slack_external=<latest-ts> \
  --source linear=<latest-updated-at>
```

Normal curate takes over from here — the state file's timestamps become its implicit `--since` on the next run.

## Gotchas

- **Raised then made in the same source.** Don't file both `decision-raised` and `decision-made` — if the question was asked and answered in the same meeting, file only the `decision-made`. `from` points to the meeting wikilink, not a non-existent raised entry.
- **`retires` rules are strict.** `decision-made` → `decision-made` only. Actions.retires → `[act-NNN]` only. **Never** target MD entities (`[req-NNN]`, `[risk-NNN]`, `[meet-NNN]`) in any `retires` array — MDs retire via frontmatter. The validator catches this, but the plan shouldn't propose it.
- **Linear tickets are bare tokens.** `FDSE-1509`, not `[FDSE-1509]`. Place them inline in `context`/`what` or in `links` arrays as plain strings.
- **KST everywhere, no offset written.** Every JSONL `when` is naive ISO 8601 (`YYYY-MM-DDTHH:MM:SS`) — KST is implicit, never write `+09:00`. Meeting dates are date-only. Get "now" from the shell, not from training data:

  ```bash
  python -c "from datetime import datetime, timezone, timedelta; print(datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%dT%H:%M:%S'))"
  ```

- **Milestone shifts vs. trivial date tweaks.** Only log `milestone-shifted` when the shift has a reason worth preserving (scope change, blocker, customer request). Holiday reshuffles go directly to `timeline.yaml`.
- **Milestone actions must sync `timeline.yaml` in the same plan.** A `type: milestone` action moves its `ms-NNN` from `milestones:` to `done:` with `completed: YYYY-MM-DD`. A `type: milestone-shifted` action updates the milestone's `when:` date. Curate must not produce milestone events without touching `timeline.yaml` — they're two halves of one change.
- **Meetings don't enumerate outputs.** Decisions point to meetings via `from`; meetings don't list their decisions. Obsidian backlinks handle reverse lookup.
- **Vault location for scripts.** All script invocations resolve the project via `$PROJECTIVITY_VAULT` or `cwd/Project_OS`. If that fails, pass `--path "<absolute>/projects/<slug>"` instead of `--project <slug>`.
- **No placeholders in backfill proposals.** Sequential window execution + coordinator-maintained in-memory ID counters means every subagent works with real IDs from its allocated range. If you find yourself inventing a placeholder token for a cross-window reference, back up — either the ref is to a *prior* window (coordinator already has that real ID and should pass it in), or to a *future* window (which can't exist because future proposals haven't been made yet). Forward refs in time don't occur in practice — you can't make a decision about a question that hasn't been asked.
- **Don't over-share context with backfill subagents.** Pass the window's sources, the allocated ID starting points, and the still-open items summary — that's it. Do **not** pass prior windows' full proposals, pre-backfill vault contents, or chat history. The subagent reads the vault directly (`Read`, `Bash`, `link_graph.py`) when it needs pre-backfill context. Over-sharing defeats the context-hygiene reason we used subagents to begin with.
- **Floor the probe at `overview.md:when_created`.** A Slack channel might have existed for years before the project — any data older than project creation is almost certainly noise. Don't ingest it. `when_created` is the authoritative pre-project boundary.

## Verification

Run before declaring done. The aim is to catch bad writes before the next skill consumes them — `audit` will surface them later, but cheaper to fix in the same session:

1. **Re-validate every JSONL line you wrote.** The pre-write check in step 8 covers proposed lines; this confirms what actually landed on disk:
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/actions.jsonl"
   ```
   Exit 0 means clean. Any non-zero is a bug introduced by the write — surface to the PM, don't silently retry.

2. **Cross-references resolve.** For every new bracket ID you set as a `from`/`links`/`retires` target, confirm the target exists. `link_graph.py <id> --project <slug>` is the cheapest way — if the target is missing, `incoming` will be empty for an ID you just wrote a reference to.

3. **No raised+made pair for the same question in one source.** Re-read your written decisions: if both a `decision-raised` and a `decision-made` carry `from` pointing at the same meeting and the made one resolves a question that wasn't asked elsewhere, you double-filed. The convention is "made-only when raised and made happen in the same source".

4. **Aging-pending nudge fired (if applicable).** If you added a new `decision-raised`, the SKILLS-GUIDE expects you to have shown the PM existing aging-pending decisions first (see `aging_pending.py --threshold 14`). Note in the output whether you did.

## Output

A structured plan shown to the PM (per `templates/proposal-preview.md`), then on approval: the list of files written with their paths, the verification results above, and any unresolved tokens or uncertain filings for the PM to follow up on.
