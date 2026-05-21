#!/usr/bin/env python3
"""PreToolUse gate — health check first, then frontmatter correction if clean.

Flow:
  1. Health check: review code against SOLID/DRY rules.
     - Violations found  → deny immediately (no frontmatter cost wasted).
     - Clean or error    → proceed to step 2.

  2. Frontmatter correction: fix solid-description if needed.
     - Corrected         → allow with updatedInput (clean code, clean description).
     - Already clean     → allow silently.

Sequential ordering ensures:
  - Frontmatter only runs on code that passed health (correct semantic context).
  - No wasted LLM call on frontmatter when the write will be denied anyway.
  - The corrected description reflects the code that will actually be written.

Fails open on infrastructure errors in either check.
"""

import difflib
import json
import re
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# Low-risk edit detection — skip health check for structural-only changes
# ---------------------------------------------------------------------------

_SOLID_BLOCK_RE = re.compile(r"^\s*/\*\*\s*\n(?:[ \t]+solid-[^\n]+\n)+[ \t]*\*/\s*\Z")


def _is_frontmatter_only(old: str, new: str) -> bool:
    """Both old and new are purely /** solid-* */ blocks — no Swift code changed."""
    return bool(_SOLID_BLOCK_RE.match(old.strip())) and bool(_SOLID_BLOCK_RE.match(new.strip()))


def _is_reorder(old: str, new: str) -> bool:
    """Same tokens in different order — argument reorder, function reorder, import sort."""
    return sorted(re.findall(r'\w+', old)) == sorted(re.findall(r'\w+', new))


def _is_rename(old: str, new: str) -> bool:
    """Same non-identifier skeleton — only names changed (rename refactor)."""
    skeleton = lambda s: re.sub(r'\b\w+\b', 'X', s)
    return skeleton(old) == skeleton(new)


def _is_low_risk_edit(old: str, new: str) -> bool:
    """Return True if the edit is structural-only and cannot introduce SOLID violations.
    Note: frontmatter-only changes skip health but NOT frontmatter correction."""
    return _is_frontmatter_only(old, new) or _is_reorder(old, new) or _is_rename(old, new)


def _diff_chunks(old_content: str, new_content: str) -> tuple:
    """Return (old_changed, new_changed) — only the lines that actually changed."""
    old_lines = old_content.splitlines()
    new_lines = new_content.splitlines()
    old_changed, new_changed = [], []
    for tag, i1, i2, j1, j2 in difflib.SequenceMatcher(None, old_lines, new_lines).get_opcodes():
        if tag == "equal":
            continue
        old_changed.extend(old_lines[i1:i2])
        new_changed.extend(new_lines[j1:j2])
    return "\n".join(old_changed), "\n".join(new_changed)

HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import code_health_check as health
import validate_swift_frontmatter as frontmatter
from hook_utils import make_hook_gate
from hc_violation_parser import ViolationParser

_gate = make_hook_gate()


def _log(msg: str) -> None:
    _gate.log(msg)

_FRONTMATTER_RE = re.compile(
    r"/\*\*\s*\n((?:[ \t]+solid-[^\n]+\n)+)[ \t]*\*/",
    re.MULTILINE,
)


def _extract_frontmatter_blocks(content: str) -> list:
    return [m.group(0) for m in _FRONTMATTER_RE.finditer(content)]


def _run_health(content: str, file_path: str, language: str, parent_session_id: str):
    """Returns list of violation dicts, [] if clean, None on error."""
    return health._check(content, file_path, language, parent_session_id)


def _run_frontmatter(content: str, parent_session_id: str, file_path: str):
    """Returns corrected content if changed, original content if clean, None on error."""
    if "solid-description:" not in content:
        return content
    return frontmatter.fix_with_claude(
        content,
        parent_session_id=parent_session_id,
        file_path=file_path,
    )


def _allow() -> None:
    _gate.allow()


def _allow_corrected(tool_name: str, tool_input: dict, corrected: str, existing_content: str = "") -> None:
    updated = dict(tool_input)
    if tool_name == "Write":
        updated["content"] = corrected
    elif existing_content:
        # content was simulated from the full existing file — replace the whole file
        # so the Edit tool doesn't insert corrected (full file) where old_string was (small snippet).
        updated["old_string"] = existing_content
        updated["new_string"] = corrected
        updated.pop("replace_all", None)
    else:
        # File was unreadable; content == new_string, corrected is the corrected snippet.
        updated["new_string"] = corrected
    _gate.allow_with_update(updated)


def _deny(violations: list) -> None:
    parts = [
        ViolationParser().format_block_reason(violations),
        "The file was NOT written. You MUST fix all violations above and write the corrected version before continuing.",
    ]
    reason = "[health-check] " + "\n\n".join(parts)
    _gate.block(reason)


def main() -> None:
    try:
        event = json.loads(sys.stdin.read())
    except (json.JSONDecodeError, ValueError):
        _allow()
        return

    tool_name = event.get("tool_name", "")
    tool_input = event.get("tool_input") or {}
    file_path = tool_input.get("file_path", "")
    parent_session_id = event.get("session_id", "")

    ext = Path(file_path).suffix.lower()
    if ext not in health.SUPPORTED_EXTENSIONS:
        _allow()
        return

    existing = ""
    low_risk = False
    if tool_name == "Write":
        content = tool_input.get("content", "")
        try:
            existing = Path(file_path).read_text(encoding="utf-8")
            old_chunk, new_chunk = _diff_chunks(existing, content)
            if old_chunk or new_chunk:
                low_risk = _is_low_risk_edit(old_chunk, new_chunk)
            else:
                low_risk = True  # identical content — nothing changed
        except OSError:
            pass  # new file — run full health check
    elif tool_name == "Edit":
        old_string = tool_input.get("old_string", "")
        new_string = tool_input.get("new_string", "")
        replace_all = tool_input.get("replace_all", False)
        low_risk = _is_low_risk_edit(old_string, new_string)
        try:
            existing = Path(file_path).read_text(encoding="utf-8")
            content = existing.replace(old_string, new_string) if replace_all \
                      else existing.replace(old_string, new_string, 1)
        except OSError:
            content = new_string  # file unreadable — fall back to snippet only
    else:
        _allow()
        return

    ext = Path(file_path).suffix.lower()
    language = health.SUPPORTED_EXTENSIONS.get(ext)
    file_name = Path(file_path).name

    run_health = language is not None and not low_risk
    run_frontmatter = "solid-description:" in content

    if not run_health and not run_frontmatter:
        _allow()
        return

    name = file_name
    _log(f"INVOKE {name}: health={run_health} frontmatter={run_frontmatter}")

    # ── Step 1: health check ────────────────────────────────────────────────
    violations = None
    if run_health:
        try:
            violations = _run_health(content, file_path, language, parent_session_id)
        except Exception as e:
            _log(f"FAIL health {name}: {e}")

        if violations is None:
            _log(f"FAILOPEN {name}: health check returned None (subprocess error)")
        elif violations:
            _log(f"DENY {name}: {len(violations)} violation(s)")
            _deny(violations)

    # ── Step 2: frontmatter correction (only reached if health passed) ──────
    corrected = None
    if run_frontmatter:
        try:
            corrected = _run_frontmatter(content, parent_session_id, file_path)
        except Exception as e:
            _log(f"FAIL frontmatter {name}: {e}")

    if corrected is not None and corrected != content:
        _log(f"CORRECTED {name}: frontmatter updated")
        _allow_corrected(tool_name, tool_input, corrected, existing_content=existing)
    else:
        if run_health or run_frontmatter:
            _log(f"CLEAN {name}")
        _allow()


if __name__ == "__main__":
    main()
