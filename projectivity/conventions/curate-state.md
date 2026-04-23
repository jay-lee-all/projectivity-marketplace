# Curate State — per-project incremental sync file

Machine-maintained per-project file that tracks the latest timestamp consumed from each source. Lets curate avoid duplicates across runs without the PM having to remember what was filed. Loaded by `scaffold` (creates empty at project setup) and `curate` (reads at run start, updates at run end).

## Location

`projects/<slug>/core/curate-state.yaml` — part of the canonical project shape (see `conventions/project-shape.md`).

## Schema

```yaml
# Machine-maintained. Per-source timestamps of the latest items consumed by curate.
# Read at the start of every curate run; updated after a successful write.
# Scaffold initializes this file with empty per-source stubs based on overview.md.

sources:
  slack_internal:
    channel_id: C0AM8QBGP4J
    last_message_ts: null         # naive ISO 8601 KST; null = never curated
  slack_external:
    channel_id: C0XYZ0000
    last_message_ts: null
  linear:
    project_name: Jobis
    last_issue_updated_at: null
  email:
    last_thread_ts: null          # optional; omit the key entirely if not a source

last_run:
  mode: backfill | incremental    # null before the first successful run
  when: 2026-04-22T18:30:00       # naive ISO 8601 KST; null before first run
```

## Contract

- **Read at start.** Curate reads this file first thing every run. Each source's `last_..._ts` is the implicit lower bound for that source; `now()` is the upper bound.
- **CLI overrides are explicit.** `--since <date>` on the CLI overrides all sources to that timestamp; `--until <date>` overrides the upper bound. Without overrides, the file is authoritative.
- **Inline sources bypass the file.** If the PM pastes a Slack thread or names a meeting MD directly in the curate invocation, the state file is not consulted *for that source* — inline input is always authoritative.
- **Update at end.** After a successful write, curate updates each source's `last_..._ts` to the timestamp of the latest item it consumed from that source during this run. If curate consumed nothing from a given source, that source's timestamp is unchanged.
- **`last_run` captures mode + time.** `last_run.mode` is `backfill` for `--backfill` invocations, `incremental` otherwise. `last_run.when` is the completion time in naive KST. Used by `brief` and `audit` to reason about when the vault was last touched.

## Rules

- **Never edited by hand.** Curate is the only writer after scaffold's initial seed.
- **Missing keys are allowed.** A project with no email source simply omits the `email` block. The schema is additive, not exhaustive.
- **`null` means "never curated from this source."** Curate treats this as "no lower bound" — the source's earliest relevant item becomes the floor (see `curate/SKILL.md` backfill mode, phase 1).
- **Timestamps are naive ISO 8601 KST**, same as `when` fields elsewhere (`conventions/timestamps.md`). No `+09:00` suffix.

## Cross-references

- **Scaffold** creates this file from `skills/scaffold/templates/curate-state.yaml`, seeded with channel IDs and project name from elicitation.
- **Curate** reads at step 0, updates at step 11 (see `skills/curate/SKILL.md`).
- **Shape authority** is `conventions/project-shape.md`, which lists `curate-state.yaml` under `core/`.
