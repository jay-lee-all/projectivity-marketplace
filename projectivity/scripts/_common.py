"""Shared helpers for Projectivity scripts.

Keep this file tiny. Scripts should stay independently readable; only
genuinely duplicated logic belongs here (path resolution, JSONL iteration,
frontmatter loading).
"""
from __future__ import annotations

import json
import os
import re
import sys
from datetime import date, datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Iterator

try:
    import frontmatter  # python-frontmatter
except ImportError:  # pragma: no cover - surfaced as runtime error
    frontmatter = None  # type: ignore[assignment]

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


KST = timezone(timedelta(hours=9))

BRACKET_ID_RE = re.compile(r"\[(dec|act|req|meet|risk)-\d{3,5}\]")
CROSSPROJ_BRACKET_RE = re.compile(r"\[prj-\d{3}:(dec|act|req|meet|risk)-\d{3,5}\]")
WIKILINK_RE = re.compile(r"\[\[([^\]]+)\]\]")
# Linear tickets are bare tokens; prefix validity is checked against team.yaml.
LINEAR_CANDIDATE_RE = re.compile(r"\b([A-Z]{2,5})-(\d{3,5})\b")


def fail(msg: str, code: int = 1) -> None:
    """Print a JSON error and exit."""
    sys.stderr.write(json.dumps({"error": msg}) + "\n")
    sys.exit(code)


def _json_default(o: Any) -> Any:
    # python-frontmatter returns datetime.date for YAML date fields; stringify
    # these (and datetime / Path) so emit() can serialize frontmatter as-is.
    if isinstance(o, datetime):
        return o.isoformat()
    if isinstance(o, date):
        return o.isoformat()
    if isinstance(o, Path):
        return str(o)
    raise TypeError(f"Object of type {type(o).__name__} is not JSON serializable")


def emit(obj) -> None:
    """Print JSON result to stdout (one-shot, non-streaming)."""
    sys.stdout.write(
        json.dumps(obj, ensure_ascii=False, indent=2, default=_json_default) + "\n"
    )


def project_root(project: str | None, explicit_path: str | None = None) -> Path:
    """Resolve the project directory.

    Precedence: --path > --project relative to $PROJECTIVITY_VAULT > cwd/Project_OS/<project>.
    """
    if explicit_path:
        p = Path(explicit_path).expanduser().resolve()
        if not p.is_dir():
            fail(f"path does not exist or is not a directory: {p}")
        return p

    vault_env = os.environ.get("PROJECTIVITY_VAULT")
    if vault_env:
        vault = Path(vault_env).expanduser().resolve()
    else:
        # Fallback: sibling Project_OS under CWD.
        vault = Path.cwd() / "Project_OS"

    if not project:
        fail("either --path or --project is required (or set $PROJECTIVITY_VAULT)")

    candidate = vault / "projects" / project
    if not candidate.is_dir():
        candidate = vault / project  # looser fallback
    if not candidate.is_dir():
        fail(f"project directory not found under {vault}: {project}")
    return candidate


def iter_jsonl(path: Path, skip_schema: bool = True) -> Iterator[dict]:
    """Yield parsed JSONL records. By convention the first line is `_schema`."""
    if not path.exists():
        return
    with path.open("r", encoding="utf-8") as fh:
        for i, line in enumerate(fh):
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError as e:
                fail(f"{path}:{i + 1}: invalid JSON — {e}")
            if skip_schema and isinstance(obj, dict) and "_schema" in obj:
                continue
            yield obj


def load_frontmatter(path: Path) -> tuple[dict, str]:
    """Return (frontmatter_dict, body) for an MD file."""
    if frontmatter is None:
        fail("python-frontmatter is required (pip install python-frontmatter)")
    post = frontmatter.load(path)
    return dict(post.metadata), post.content


def load_yaml(path: Path):
    if yaml is None:
        fail("PyYAML is required (pip install pyyaml)")
    if not path.exists():
        fail(f"YAML not found: {path}")
    with path.open("r", encoding="utf-8") as fh:
        return yaml.safe_load(fh)


def parse_kst(ts: str) -> datetime | None:
    """Parse a vault timestamp.

    Accepts:
      - date-only `YYYY-MM-DD` (interpreted as midnight KST)
      - naive ISO 8601 `YYYY-MM-DDTHH:MM:SS` (the canonical vault format —
        KST is implicit, no offset is written)
      - tz-aware ISO 8601 with `+09:00` (legacy entries written before the
        offset was dropped — still readable)

    Returns a tz-aware datetime in KST, or None on parse failure.
    """
    if not ts:
        return None
    try:
        if len(ts) == 10 and ts[4] == "-" and ts[7] == "-":
            return datetime.fromisoformat(ts).replace(tzinfo=KST)
        dt = datetime.fromisoformat(ts)
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=KST)
        return dt
    except ValueError:
        return None


def now_kst() -> datetime:
    return datetime.now(KST)


def now_kst_str() -> str:
    """Canonical 'now' string for the vault: naive ISO 8601, KST implicit."""
    return datetime.now(KST).strftime("%Y-%m-%dT%H:%M:%S")
