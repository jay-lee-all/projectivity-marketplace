# Projectivity

Runtime plugin for the Project_OS vault. Six skills, one deterministic Python layer, conventions-on-demand via a resolver.

## Layout

```
projectivity/
├── .claude-plugin/plugin.json     # manifest
├── resolver.md                    # skill → conventions routing
├── conventions/*.md               # domain rule docs, loaded on demand
├── skills/{meeting,curate,brief,query,audit,scaffold}/SKILL.md
├── scripts/*.py                   # deterministic lookups, no LLM, no writes
├── hooks/hooks.json               # placeholder; v1 ships without hooks
└── requirements.txt               # Python dependencies
```

## Install

This plugin is distributed through the `allganize-projectivity` marketplace (the `.claude-plugin/marketplace.json` one directory up from this README).

```
/plugin marketplace add jay-lee-all/projectivity-marketplace
/plugin install projectivity@allganize-projectivity
/reload-plugins
```

Then every PM invokes skills as `/projectivity:meeting`, `/projectivity:curate`, etc.

## Scripts

Python 3.10+. Dependencies are pinned in `requirements.txt` at the plugin root. Install once per PM machine (or per venv) before using the plugin:

```
pip install -r requirements.txt
```

The two runtime dependencies are:

- `python-frontmatter` — MD frontmatter parsing
- `PyYAML` — team.yaml / contacts.yaml / timeline.yaml

Every script takes arguments on the CLI and emits JSON on stdout. No script writes to the vault; skills do that, after PM confirmation.

## Vault assumption

Scripts expect to run against a Project_OS vault: a directory containing `team.yaml`, optional `contacts.yaml`, and `projects/<slug>/` subdirectories. The vault root is resolved via `$PROJECTIVITY_VAULT`, `--path`, or `--project` (per script).
