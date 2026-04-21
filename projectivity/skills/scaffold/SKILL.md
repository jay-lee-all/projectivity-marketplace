---
description: Create new vault structure — a new project, a new team member entry, new requirement/risk skeletons, or bootstrap a fresh vault. Operational, not analytical — it sets up empty-but-correct scaffolding so curation can fill it. Use when adding a project, onboarding a teammate, or starting a new deliverable that needs an MD stub.
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

## Conventions Loaded at Skill Start

**Always:** `conventions/references.md`, `conventions/timestamps.md`.

**Conditionally:**
- New project or fresh JSONL → `conventions/jsonl.md` (for the `_schema` first line).
- New requirement → `conventions/md-requirements.md`.
- New risk → `conventions/md-risks.md`.
- New meeting scaffold (rare — usually `meeting` covers this) → `conventions/md-meetings.md`.

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

   - **New requirement:** Frontmatter with `id`, `title`, `status: active`, `when_created` (KST now), `who`, `project`. Body skeleton: `## Spec`, `## Updates`.

   - **New risk:** Frontmatter with `id`, `title`, `when_surfaced` (KST now), empty `when_resolved`, `who`, `category`. Body: opening line + reference to what surfaced it.

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

## Output

A list of files/folders created, with the paths. No JSONL or MD substance beyond the scaffold shape.
