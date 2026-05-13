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

import json
import re
import sys
import time
from pathlib import Path

_LOG = Path.home() / ".claude" / "solid-coder-gate.log"


def _log(msg: str) -> None:
    try:
        with _LOG.open("a") as f:
            f.write(f"{time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime())} {msg}\n")
    except Exception:
        pass


HOOKS_DIR = Path(__file__).resolve().parent
if str(HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(HOOKS_DIR))

import code_health_check as health
import validate_swift_frontmatter as frontmatter

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
    sys.exit(0)


def _allow_corrected(tool_name: str, tool_input: dict, corrected: str) -> None:
    input_key = "content" if tool_name == "Write" else "new_string"
    updated = dict(tool_input)
    updated[input_key] = corrected
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "allow",
            "updatedInput": updated,
        }
    }))
    sys.stdout.flush()
    sys.exit(0)


def _deny(violations: list) -> None:
    parts = [
        health._format_block_reason(violations),
        "The file was NOT written. You MUST fix all violations above and write the corrected version before continuing.",
    ]
    reason = "[health-check] " + "\n\n".join(parts)
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
    }))
    sys.stdout.flush()
    sys.exit(0)


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

    if tool_name == "Write":
        content = tool_input.get("content", "")
    elif tool_name == "Edit":
        content = tool_input.get("new_string", "")
    else:
        _allow()
        return

    if not file_path.endswith(".swift"):
        _allow()
        return

    ext = Path(file_path).suffix.lower()
    language = health.SUPPORTED_EXTENSIONS.get(ext)
    file_name = Path(file_path).name
    long_enough = content.count("\n") >= health.MIN_LINES

    run_health = language is not None and long_enough
    run_frontmatter = "solid-description:" in content

    if not run_health and not run_frontmatter:
        _allow()
        return

    name = file_name

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
        _allow_corrected(tool_name, tool_input, corrected)
    else:
        if run_health or run_frontmatter:
            _log(f"CLEAN {name}")
        _allow()


if __name__ == "__main__":
    main()
