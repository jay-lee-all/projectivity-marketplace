# Timestamps

All timestamps across the vault follow one rule set. Loaded by every skill that writes.

## Timezone: KST, always (implicit)

Korea Standard Time. The team is in Korea, so every timestamp is KST and the offset is **never written**. A naive ISO 8601 string like `2026-04-22T11:07:36` is read as KST by every skill and script.

Even for events that happened in a different timezone — if a customer call is at 10am ET, record the KST equivalent (`2026-03-15T00:00:00` = midnight KST). Single-timezone data makes date-range queries reliable; mixed timezones make them fragile.

Do not write `+09:00`, `Z`, or any other offset. The convention is "no offset, ever".

## Formats by file type

| File | Field | Format | Example |
| --- | --- | --- | --- |
| `decisions.jsonl`, `actions.jsonl` | `when` | naive ISO 8601 (KST implied) | `2026-02-20T14:30:00` |
| `meetings/*.md` frontmatter | `when` | date only | `2026-02-20` |
| `requirements/*.md` frontmatter | `when_created`, `when_completed` | naive ISO 8601 (KST implied) | `2026-02-20T14:30:00` |
| `risks/*.md` frontmatter | `when_surfaced`, `when_resolved` | naive ISO 8601 (KST implied) | `2026-03-18T13:00:00` |
| `timeline.yaml` | `date`, `completed`, `dropped_on` | date only | `2026-05-15` |

- JSONL and most MD frontmatter timestamps carry minute precision.
- Meeting frontmatter `when` is **date-only**. Minute-precision events that happened *during* the meeting go on the JSONL entries the curation skill produces (decisions, actions), not on the meeting itself.
- `timeline.yaml` is date-only because it represents day-level anchors.

## Precision

Minute precision is enough for JSONL and MD lifecycle timestamps. Seconds can be `:00` unless meaningful. Sub-minute precision is never needed.

## Semantics

`when` (and its MD equivalents) records **when the event occurred**, not when it was logged. When curating a meeting that happened yesterday, use yesterday's date/time, not the current time.

Meeting-derived entries (decisions, actions extracted from a meeting) reuse the meeting's date with an appropriate time — typically the meeting start time, or a reasonable refinement if the source indicates when in the meeting the decision/action surfaced.

## Current time for "now" operations

When a skill needs "now" (e.g. logging a `task-done` the PM just completed), use the system clock's KST time. Do not fabricate. Shell one-liner the curation skill can call:

```
python -c "from datetime import datetime, timezone, timedelta; print(datetime.now(timezone(timedelta(hours=9))).strftime('%Y-%m-%dT%H:%M:%S'))"
```

The `strftime` ends at seconds — no `+09:00` suffix.

## Validation

- [ ] No JSONL/MD timestamp string carries an offset (`+09:00`, `Z`, etc.).
- [ ] Meeting frontmatter `when` is date-only (10 chars: `YYYY-MM-DD`), no time.
- [ ] timeline.yaml dates are date-only.
- [ ] Minute-precision timestamps are exactly 19 chars: `YYYY-MM-DDTHH:MM:SS`.
