# Daily Priority Briefing

A single-page view of where the PM's attention is needed today. Multi-project: iterate over every directory under `projects/` unless `--project` is passed.

## Sections (in order)

### 1. What's on fire
Open risks where `when_surfaced` ≥ 7 days ago and `when_resolved` is empty, grouped by project. Include category and the 1-line opener.

Data:
```bash
python "$CLAUDE_PLUGIN_DIR/scripts/frontmatter_index.py" \
  "projects/<slug>/risks" --filter when_resolved=
```

Format: `**{project}** — [[risks/{slug}]] ({category}, {age_days}d): opening line`.

### 2. Decisions waiting on me
Aging `decision-raised` past a 14-day threshold, grouped by project. Cross-reference `who` against the current PM — if the PM is the owner or raised it, surface it prominently.

Data:
```bash
python "$CLAUDE_PLUGIN_DIR/scripts/aging_pending.py" --project <slug> --threshold 14
```

Format: `**{project}** [{dec-NNN}] ({age_days}d): question`.

### 3. Tasks I committed to
Open `task-created` entries with `who` matching the current PM, across all projects, oldest first. Cap at 10.

Data:
```bash
python "$CLAUDE_PLUGIN_DIR/scripts/aging_pending.py" --project <slug> --threshold 0 --include-tasks
```

Filter `aging_tasks` where `who` resolves to the PM.

### 4. What closed recently
`decision-made` entries with `when` in the last 3 days. Brief — 1 line each, grouped by project. Gives the PM a quick recap of momentum.

Data:
```bash
python "$CLAUDE_PLUGIN_DIR/scripts/active_decisions.py" --project <slug> --since <3-days-ago>
```

### 5. Upcoming milestones (next 14 days)
Read `projects/<slug>/timeline.yaml`; filter `milestones:` where `date` ≤ today+14. Include target date and owner.

## Footer

`_Generated {YYYY-MM-DD HH:MM}. Data from {N} projects._` (time is KST — see `conventions/timestamps.md`; no offset suffix.)

## Notes for the skill

- If a section has no rows, include the heading and write `None.` — never omit silently.
- Sort each section by urgency: older first for 1-3, closest date first for 4-5.
- Keep the whole briefing under one screen's worth of reading; cap each section at 5-7 items.
