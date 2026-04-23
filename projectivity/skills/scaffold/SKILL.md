---
description: Create new vault structure — a new project, a new team member entry, requirement or risk skeletons, or bootstrap a fresh vault. Use when starting a new deliverable: "set up the new Hyundai project", "add Meera to the team", "stub out the FAQ Agent requirement". Empty-but-correct scaffolding only — curation fills the substance later.
hooks:
  - conventions/references.md
  - conventions/timestamps.md
  - conventions/project-shape.md
---

# scaffold — new structure

## When to Use

Structure doesn't yet exist and needs to. Typical triggers:

- New project: create `projects/{slug}/` with the full canonical shape from `conventions/project-shape.md` — `overview.md` at the root, `core/` holding the five structured data files (decisions.jsonl, actions.jsonl, timeline.yaml, contacts.yaml, curate-state.yaml), plus four content subfolders (meetings, requirements, risks, _files).
- New team member: append a record to `team.yaml`.
- New requirement: create `requirements/{slug}.md` with complete frontmatter and a Spec skeleton.
- New risk: create `risks/{slug}.md` with frontmatter and an opening line.
- Fresh vault bootstrap: `Project_OS/` with top-level `team.yaml`, `contacts.yaml`, and a first project folder.

Not for: curation (`curate`), templated status (`brief`), or answering questions (`query`).

## Conventions

Frontmatter `hooks` declares the always-load set (`references.md`, `timestamps.md`, `project-shape.md`). The canonical per-project layout lives in `project-shape.md` — scaffold executes that shape, it doesn't redefine it. Conditionally load:

- `conventions/jsonl.md` — new project or fresh JSONL (for the `_schema` first line).
- `conventions/md-requirements.md` — new requirement.
- `conventions/md-risks.md` — new risk.
- `conventions/md-meetings.md` — new meeting scaffold (rare; usually `meeting` covers this).

## Workflow

1. **Elicit the scaffold target and its fields.** For a **new project**, use `AskUserQuestion` to collect the field set below. Pre-fill any values already supplied in the invocation; only prompt for the gaps.

   **Required (block until supplied):**
   - `slug` — lowercase kebab-case (e.g., `jobis`, `hyundai-motors`)
   - `linear_project_name` — exact Linear project name

   **Prompt-for-all, accept blanks:**
   - `description` — one-line purpose ("on-prem deployment for Jobis & Villains")
   - `customer_org` — English + Korean name where applicable
   - `internal_slack` — channel ID + name (Allganize-side coordination channel)
   - `external_slack` — channel ID + name (customer-facing channel, if any)
   - `linear_ticket_prefix` — e.g., `FDSE`, `AI` (informs curate's bare-token recognition)
   - `lead_pm` — name matching `team.yaml`
   - `customer_contacts` — optional paste of names + roles; seeds `contacts.yaml`
   - `has_backlog` — yes/no; gates the end-of-scaffold `curate --backfill` handoff

   **Never fabricate defaults for customer-facing fields.** If the PM hasn't supplied the external Slack channel or the customer org, leave them blank — scaffold surfaces the gap as `TBD` in `overview.md`. A guessed Slack ID is strictly worse than a blank: every downstream skill will believe it.

   For **other scaffold targets**, ask the minimal set that target needs:
   - New requirement: title, project, 1-line intent.
   - New risk: title, category, project, 1-line opener.
   - New team member: name + the fields in `team.yaml`.
   - Fresh vault: confirm the target path (`$PROJECTIVITY_VAULT` or an explicit path).

2. **Check for collisions.** Folder or file already exists? Ask before overwriting. Scaffold is never a destructive operation.

3. **Build the scaffold per its convention.** Each target has its own shape — see the loaded conventions. Common rules:

   - **New project.** Build the canonical shape per `conventions/project-shape.md` — all entries created at scaffold time:

     ```
     projects/<slug>/
       overview.md                  # from templates/overview.md, elicitation-filled
       core/
         decisions.jsonl            # first line: {"_schema": "decisions-v1"}
         actions.jsonl              # first line: {"_schema": "actions-v1"}
         timeline.yaml              # header + empty milestones/done/dropped/deadlines
         contacts.yaml              # from templates/contacts.yaml, seeded if customer_contacts given
         curate-state.yaml          # from templates/curate-state.yaml, seeded from source elicitation
       meetings/                    # empty
       requirements/                # empty
       risks/                       # empty
       _files/                      # empty
     ```

     `project-shape.md` is the authority on this list. Don't skip subfolders because they have no content — `brief`, `query`, and `audit` all glob into them; present-but-empty is the stable contract.

   - **New team member:** Append to the existing `team.yaml` list. Fields per existing records: `name`, `email`, `slack`, `slack_name`, `github`, `linear`, `team`, `role`. Don't reorder existing entries.

   - **New requirement:** Frontmatter with `id`, `title`, `status: active`, `when_created` (now, naive ISO 8601 per `timestamps.md`), `who`, `project`. Body skeleton: `## Spec`, `## Updates`.

   - **New risk:** Frontmatter with `id`, `title`, `when_surfaced` (now, naive ISO 8601 per `timestamps.md`), empty `when_resolved`, `who`, `category`. Body: opening line + reference to what surfaced it.

4. **Get IDs from `next_id.py`.** Never invent sequential IDs.

5. **Get "now" from the shell, not training data.** The Python one-liner in `conventions/timestamps.md` is the authoritative source.

6. **Confirmation.** Show the full scaffold plan (paths and content) to the PM before writing. A new-project scaffold creates the full layout in `project-shape.md` — `overview.md`, the `core/` directory and its five files (decisions, actions, timeline, contacts, curate-state), and four content subfolders. Don't write any until approved.

7. **Curation fills substance, not shape.** Scaffold populates `overview.md` and `contacts.yaml` from elicitation — those two files define the project's identity and are scaffold's job. Every other file stays a shell: JSONLs carry only the `_schema` line; `timeline.yaml` has empty lists; requirement Specs are `TBD`; risks have only an opener. Decisions, actions, meeting notes, and substantive bodies are curation's job.

8. **Post-write handoff.** If the PM answered `has_backlog: yes` during elicitation, close the output with:

   > This project has existing history to backfill. In a fresh session, run:
   > `/projectivity:curate --backfill <slug>`
   > Curate reads sources (Slack channels, Linear project) from `overview.md` and the time range from `core/curate-state.yaml`, so no flags are needed for the common case. Use `--since YYYY-MM-DD` / `--until YYYY-MM-DD` only to narrow the range.

   Always include a one-line vault-hygiene note:

   > Add `projects/*/_files/` to your vault's `.gitignore` if not already present — scaffold creates `_files/` intentionally empty for attachments, and the plugin cannot edit your vault's gitignore for you.

## Gotchas

- **Never fabricate customer-facing fields.** If elicitation didn't yield an external Slack channel or a customer org name, leave them as `TBD` in `overview.md`. A plausible-looking but guessed Slack ID is actively destructive — it ends up in curate's source lists, and every downstream skill believes it. Blank surfaces the gap; invented data hides it.
- **All four canonical subfolders get created.** `meetings/`, `requirements/`, `risks/`, `_files/`. `conventions/project-shape.md` is the authoritative list. "No empty structure" applies to *speculative* folders, not to the canonical contract every skill reads against.
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
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/decisions.jsonl"
   python "$CLAUDE_PLUGIN_DIR/scripts/validate_jsonl.py" "projects/<slug>/core/actions.jsonl"
   ```
   Exit 0 confirms the `_schema` line is the only content and parses correctly. A broken scaffold means `curate` will silently append to a malformed file.

2. **New MD stubs parse as frontmatter + body.** For any new requirement or risk:
   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/frontmatter_index.py" \
     "projects/<slug>/requirements" --filter id=<new-req-id>
   ```
   Should return exactly one entry with the full frontmatter. Unquoted values or wrong indentation break this quietly.

3. **Expected directory shape exists per `project-shape.md`.** After a new-project scaffold, the directory listing should show `overview.md`, a `core/` subfolder containing `decisions.jsonl`, `actions.jsonl`, `timeline.yaml`, `contacts.yaml`, and `curate-state.yaml`, plus the four content subfolders `meetings/`, `requirements/`, `risks/`, `_files/`. Missing any of these means `brief`/`query`/`audit` will fail later with confusing path errors.

## Output

A list of files/folders created, with the paths, plus the verification results above. No JSONL or MD substance beyond the scaffold shape.
