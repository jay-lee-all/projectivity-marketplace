---
description: Turn a meeting transcript, notes, or summary into a meeting MD under `projects/{project}/meetings/`. Precedes curate — produces only the meeting MD, never decisions/actions. Use immediately after any customer or internal meeting where the PM has raw input (transcript, audio summary, Slack recap, jotted notes). Confirmation is mandatory before writing.
---

# meeting — transcript → meeting MD

## When to Use

The PM has raw input from a meeting and needs the canonical `meetings/{YYYY-MM-DD-slug}.md` file created. This is the precursor to `curate`, which then pulls decisions/actions/risks out of that meeting MD plus any other sources.

Do **not** use this skill for:

- Extracting decisions or actions from a meeting — that's `curate`.
- Editing an existing meeting MD — read it and edit directly (convention: `md-meetings.md`).
- Routine standups with no project content — skip the skill, skip the MD.

## Conventions Loaded at Skill Start

`conventions/md-meetings.md`, `conventions/timestamps.md`, `conventions/references.md`. These are the authoritative rules for frontmatter, body, and wikilinks — consult them; do not restate their contents in this SKILL.md.

## Workflow

1. **Identify the project.** Ask the PM which project this meeting belongs to if it's ambiguous. The project determines the target directory: `projects/{project}/meetings/`.

2. **Gather prior context.** Run `meeting_context.py` to bundle the relevant prior state:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/meeting_context.py" \
     --project <slug> \
     --attendees "Jay Kim" "김철수" \
     --lookback-days 14
   ```

   Use the output (prior meetings, recent decisions, open risks, attendee-tagged tasks) to frame the new meeting in continuity — e.g. reference the previous customer meeting by wikilink, note resolved vs. still-open raised decisions.

3. **Resolve attendee names.** Raw transcripts often contain Slack IDs, email addresses, or partial names. Normalize them:

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/resolve_name.py" \
     --tokens "U093ZAFDNTB" "meera.hong@allganize.io" \
     --team "<vault>/team.yaml"
   ```

   Use the canonical `name` field in the `attendees:` list. Flag any `unresolved` tokens to the PM at confirmation time — don't silently drop them.

4. **Get the next ID.**

   ```bash
   python "$CLAUDE_PLUGIN_DIR/scripts/next_id.py" \
     --folder "projects/<slug>/meetings" --prefix meet-
   ```

5. **Draft the MD.** Produce a frontmatter block and a body following `md-meetings.md`. Body sections typically: `## Summary`, `## Topics`, one subheading per topic, links to prior artifacts.

6. **Confirmation — mandatory.** Show the complete MD to the PM. Call out:
   - Attendee resolution (especially any unresolved tokens).
   - Which prior meeting/decision/risk you chose to reference.
   - Anything ambiguous you inferred.

   Only after explicit PM approval, write the file.

7. **Do not produce decisions/actions/risks here.** Leave that to `curate`. If the PM wants to run curation on this meeting, remind them: "Run `/projectivity:curate` next and I'll pull the decisions and actions out."

## Gotchas

- **Date vs. time.** Meeting frontmatter `when` is **date-only** (`YYYY-MM-DD`). Minute-precision events go on the JSONL entries `curate` will produce, not on the meeting itself.
- **Slug stability.** Once written, the filename is an identity. Don't rename it to "improve" the slug later — that breaks wikilinks silently. Frontmatter `id` is rename-proof; the filename is not.
- **Korean names.** Transcripts frequently mix Korean and English for the same person. Use `resolve_name.py` with the Korean name as a token if it appears in `team.yaml`'s `name` field.
- **No body template.** Don't force a rigid outline — meeting content varies. The convention gives shape, not structure.
- **Skip trivial standups.** If the meeting produced nothing project-relevant, don't create an MD. Tell the PM and move on.

## Output

After confirmation and write:

- The meeting MD path (relative to vault root).
- A 1-line summary of what went in.
- A suggestion to run `curate` next if there are decisions/actions to extract.
