---
description: Template-driven briefing from vault data — daily priority, sprint-start, weekly rollup. Use when the PM wants a predictable, recurring status snapshot: "what's on my plate today", "give me my morning briefing", "what's blocking the sprint". Read-only; never writes to the vault. Pairs with scheduled invocation. For open-ended questions, use `query`.
hooks:
  - conventions/references.md
  - conventions/timestamps.md
---

# brief — template-driven briefing

## When to Use

The PM wants a **recurring, template-shaped** status view. Briefings are predictable in structure: same sections, filled with today's data. If the question is open-ended ("why did we defer the FAQ Agent?"), use `query` instead.

v1 ships with one template: `daily-priority`. Others arrive when the PM asks for them.

## Conventions

Frontmatter `hooks` declares the always-load set (`references.md`, `timestamps.md`). Conditionally load `conventions/linear-tickets.md` if the chosen template pulls Linear data.

## Workflow

1. **Pick the template.** Ask the PM which template if not specified. Current templates live in `skills/brief/templates/`:
   - `daily-priority.md` — today's priorities across open tasks, pending decisions, recent milestones.

2. **Read the template file.** Each template defines sections, data sources, and presentation order. Follow it — don't improvise structure.

3. **Pull data deterministically.** Every data section comes from a script, not from vault browsing:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/active_decisions.py" --project <slug> --since YYYY-MM-DD
   python "$CLAUDE_PLUGIN_DIR/scripts/aging_pending.py" --project <slug> --threshold 14 --include-tasks
   python "$CLAUDE_PLUGIN_DIR/scripts/frontmatter_index.py" "projects/<slug>/risks" --filter when_resolved=
   ```

   `--since` takes a date-only `YYYY-MM-DD`. `--filter when_resolved=` filters on empty values, which is how "open risks" are expressed in frontmatter. Parse the JSON and format it per the template.

4. **Cross-project vs. single-project.** Templates declare their scope. `daily-priority` is multi-project (iterate over `projects/*/`); project-specific templates take `--project`.

5. **No writes.** This skill is strictly read-only. If the briefing surfaces something that needs filing, hand off to `curate`.

6. **Present the briefing.** Return it as prose with the template's sectioning. Include a timestamp footer so the PM knows when it was generated.

## Gotchas

- **Stale data looks current.** Always include the "as of" timestamp. A briefing viewed an hour later should still show when the data was pulled.
- **Empty sections.** If a section has nothing, keep the heading and say "None." Silent omission makes it look like you forgot the section.
- **Linear data via MCP.** If a template pulls ticket status, route through the Linear MCP — don't try to guess ticket state from bracket-ID grep.
- **One template at a time.** Don't combine templates implicitly. If the PM wants two views, produce two briefings.
- **Vault location.** Scripts resolve the project via `$PROJECTIVITY_VAULT` or `cwd/Project_OS`; if they error with "project directory not found", fall back to `--path "<absolute>/projects/<slug>"`.

## Verification

Briefings are read-only, so there's less to verify than a curation write — but wrong data in a briefing is costly precisely because the PM acts on it:

1. **Every template section rendered.** If the template declares five sections, the output has five headings in that order. Empty sections say `None.` rather than being dropped.
2. **Data matches the scripts.** Counts in the briefing prose match counts in the JSON the scripts returned. If a PM sees "3 aging decisions" in the prose, `aging_pending.py` should have returned 3 aging_decisions — if there's a delta, you hand-edited something you shouldn't have.
3. **Timestamp is present and KST.** The footer shows when data was pulled, in KST. Missing timestamp is a bug — a briefing without "as of X" is indistinguishable from stale cache.

## Output

The briefing, as prose. No file written.
