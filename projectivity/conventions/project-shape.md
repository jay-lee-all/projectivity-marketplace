# Project Shape — canonical layout

The shape every project directory must have. Loaded by skills that create or validate project structure (`scaffold`, `audit`). Other skills (`curate`, `brief`, `query`) assume this shape implicitly — they read files and glob subfolders per the layout below.

## Canonical layout

```
projects/<slug>/
  overview.md                   # project context; scaffold creates from templates/overview.md
  core/
    decisions.jsonl             # first line: {"_schema": "decisions-v1"}
    actions.jsonl               # first line: {"_schema": "actions-v1"}
    timeline.yaml               # milestones: / done: / dropped: / deadlines: (all lists)
    contacts.yaml               # project-scoped contacts (customer-side, external collaborators)
    curate-state.yaml           # curate's per-source incremental state (machine-maintained)
  meetings/                     # one MD per meeting
  requirements/                 # one MD per requirement
  risks/                        # one MD per risk
  _files/                       # attachments, screenshots, PDFs
```

Six top-level entries under `projects/<slug>/`: one file (`overview.md`), one `core/` subfolder holding the structured data files, and four content subfolders. All exist from day one, even when empty.

**Why `core/`.** The files in `core/` are the project's structured, schema-bound data surface — everything skills read and write programmatically. Keeping them together under one folder separates them cleanly from the content subfolders (`meetings/`, `requirements/`, `risks/`, `_files/`), which hold authored MDs and attachments. Scripts (`active_decisions.py`, `link_graph.py`, `aging_pending.py`, `meeting_context.py`) expect this layout; passing `--project <slug>` resolves paths via `proj / "core" / "decisions.jsonl"` etc.

## Rules

- **All entries (including `core/` and its contents) are created by `scaffold`.** Empty subfolders are intentional — they're the contract every downstream skill reads against. "No empty structure" applies to *speculative* folders (don't invent `research/` for one note), not to this canonical set.
- **Don't invent new top-level per-project folders.** If a new shape is needed, update this convention first so every skill sees the same layout.
- **`overview.md` and `core/contacts.yaml` are scaffold-populated.** Their shape is defined in `projectivity/skills/scaffold/templates/`. Every other file is a shell until `curate` or `meeting` fills it.
- **`core/curate-state.yaml` is machine-maintained.** Scaffold creates it with empty per-source stubs seeded from `overview.md`. Curate is the only subsequent writer. Never edit by hand. See `conventions/curate-state.md` for the schema and contract.
- **`_files/` is for attachments.** Scaffold creates it empty. It should be listed in the vault's `.gitignore` (`projects/*/_files/`). Scaffold surfaces this as a recommendation in its output — it does **not** edit the vault's `.gitignore` directly.

## Why empty subfolders

`brief`, `query`, and `audit` all glob into these directories. A missing `risks/` produces a `FileNotFoundError` that reads like a vault bug; a present-but-empty `risks/` returns zero matches, which every skill already handles. Stable contract > rule purity.

## Cross-references

- Canonical file shapes live in:
  - `projectivity/skills/scaffold/templates/overview.md`
  - `projectivity/skills/scaffold/templates/contacts.yaml`
  - `projectivity/skills/scaffold/templates/curate-state.yaml`
  - `conventions/jsonl.md` (for `decisions.jsonl` and `actions.jsonl` first-line schemas)
  - `conventions/curate-state.md` (for `curate-state.yaml` schema and read/update contract)
- Audit validates this shape via `skills/audit/SKILL.md`; missing subfolders are a scaffold bug, not a curation one.
