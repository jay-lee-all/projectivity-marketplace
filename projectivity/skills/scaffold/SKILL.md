---
description: Create new vault structure — a new project, a new team member entry, requirement or risk skeletons, or bootstrap a fresh vault. Use when starting a new deliverable: "set up the new Hyundai project", "add Meera to the team", "stub out the FAQ Agent requirement". Empty-but-correct scaffolding only — curation fills the substance later.
hooks:
  - conventions/references.md
  - conventions/timestamps.md
---

# scaffold — new structure

## When to Use

Structure doesn't yet exist and needs to. Typical triggers:

- New project: create `projects/{slug}/` with the expected subfolders and empty JSONL files (schema line only).
- New team member: append a record to `team.yaml`.
- New requirement: create `requirements/{slug}.md` with complete frontmatter and a Spec skeleton.
- New risk: create `risks/{slug}.md` with frontmatter and an opening line.
- Fresh vault bootstrap: `Project_OS/` with top-level `team.yaml`, `contacts.yaml`, and a first project folder.

Not for: curation (`curate`), templated status (`brief`), or answering questions (`query`).

## Conventions

Frontmatter `hooks` declares the always-load set (`references.md`, `timestamps.md`). Conditionally load:

- `conventions/jsonl.md` — new project or fresh JSONL (for the `_schema` first line).
- `conventions/md-requirements.md` — new requirement.
- `conventions/md-risks.md` — new risk.
- `conventions/md-meetings.md` — new meeting scaffold (rare; usually `meeting` covers this).

## Workflow

1. **Ask what to scaffold.** If the PM says "add a new project", ask for slug, description, and initial team. If "new requirement", ask for title, project, and 1-line intent.

2. **Check for collisions.** Folder or file already exists? Ask before overwriting. Scaffold is never a destructive operation.

3. **Build the scaffold per its convention.** Each target has its own shape — see the loaded conventions. Common rules:

   - **New project:**
     ```
     projects/<slug>/
       decisions.jsonl      # first line: {"_schema": "decisions-v1"}
       actions.jsonl        # first line: {"_schema": "actions-v1"}
       meetings/            # empty
       requirements/        # empty
       risks/               # empty
       timeline.yaml        # header + empty sections
     ```

   - **New team member:** Append to the existing `team.yaml` list. Fields per existing records: `name`, `email`, `slack`, `slack_name`, `github`, `linear`, `team`, `role`. Don't reorder existing entries.

   - **New requirement:** Frontmatter with `id`, `title`, `status: active`, `when_created` (now, naive ISO 8601 per `timestamps.md`), `who`, `project`. Body skeleton: `## Spec`, `## Updates`.

   - **New risk:** Frontmatter with `id`, `title`, `when_surfaced` (now, naive ISO 8601 per `timestamps.md`), empty `when_resolved`, `who`, `category`. Body: opening line + reference to what surfaced it.

4. **Get IDs from `next_id.py`.** Never invent sequential IDs.

5. **Get "now" from the shell, not training data.** The Python one-liner in `conventions/timestamps.md` is the authoritative source.

6. **Confirmation.** Show the full scaffold plan (paths and content) to the PM before writing. A project scaffold might create 4-6 files; don't write any until approved.

7. **Do not pre-populate content.** Scaffolds are empty-but-correct. Requirements Spec sections are placeholders (`TBD`), risks have only the opener. Curation fills the substance.

## Gotchas

- **JSONL must start with `_schema`.** An empty JSONL with no schema line will fail validation. Write the `_schema` line as the first and only line of a new JSONL.
- **Don't scaffold meetings proactively.** Meetings are created from real events via the `meeting` skill, not pre-stubbed.
- **Slug conventions.** Project slugs are lowercase kebab-case. Requirement/risk slugs are descriptive: `pii-timeout-cascade`, not `risk-001`. The date isn't in the slug — it's in frontmatter.
- **team.yaml is shared.** Adding a member touches a file used by every project. Confirm with the PM that the addition is correct before writing.
- **timeline.yaml stub.** Include the expected top-level keys (`milestones:`, `done:`, `dropped:`, `deadlines:`) as empty lists so the file parses cleanly from day one.
- **Vault location.** `next_id.py` resolves paths relatively; always pass full `--jsonl` / `--folder` paths rather than project-relative ones so the scaffold can run outside the vault cwd.

## Verification

Scaffolds must leave the vault in a valid state from day one, because every other skill assumes schema-clean files. Run these checks before declaring done:

1. **New JSONL validates empty-but-schema-line.** Validate every JSONL file you created:
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/actions.jsonl"
   ```
   Exit 0 confirms the `_schema` line is the only content and parses correctly. A broken scaffold means `curate` will silently append to a malformed file.

2. **New MD stubs parse as frontmatter + body.** For any new requirement or risk:
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/frontmatter_index.py" \
     "projects/<slug>/requirements" --filter id=<new-req-id>
   ```
   Should return exactly one entry with the full frontmatter. Unquoted values or wrong indentation break this quietly.

3. **Expected directory shape exists.** After a new-project scaffold, the directory listing should show `meetings/`, `requirements/`, `risks/`, the two JSONLs, and `timeline.yaml`. Missing any of these means `brief`/`query`/`audit` will fail later with confusing path errors.

## Output

A list of files/folders created, with the paths, plus the verification results above. No JSONL or MD substance beyond the scaffold shape.
