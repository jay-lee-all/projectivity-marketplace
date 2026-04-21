# Projectivity hooks — DEFERRED for v1

`hooks.json` ships empty on purpose. Two hook patterns are designed but not yet
enabled; this note records the intent so future contributors know why the file
is empty and what the v2 additions will look like.

## 1. Skill-scoped convention loading (`SkillStart`)

When a skill fires, inject the relevant `conventions/*.md` files declared in
the resolver. Implemented as a `SessionStart`-or-`SkillStart` hook that reads
`resolver.md` and pre-loads convention content into context.

For v1, this is achieved via the explicit **Conventions Loaded at Skill Start**
section in each `SKILL.md`, which the skill body itself references. That's
model-driven rather than deterministic, but it's enough until we have real
usage data.

## 2. `PreToolUse` JSONL validation

Match `Write|Edit` on `**/*.jsonl`, run `scripts/validate_jsonl.py` on the
proposed write, exit `2` with feedback on schema violations so Claude
self-corrects before the file lands.

## Why deferred

Per `harness/plugin-design.md`, premature hooks are over-constraining. Ship
curation first, observe real failure modes, then add the hook to catch that
class of wrong.

## When enabling

Populate `hooks` per the [Claude Code hooks spec](https://docs.claude.com/en/docs/claude-code/hooks).
The empty object currently in `hooks.json` is a valid no-op placeholder.
