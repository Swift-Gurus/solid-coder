#!/usr/bin/env python3
"""PreToolUse hook — block Bash writes to source code files.

Prevents agents from using Bash to write or modify source code files
(sed -i, perl -pi, tee, redirects, etc.). Source code changes must go
through the Write or Edit tools so the pre-write quality gate can review.

Only blocks commands that target protected extensions (.swift, .kt, .java).
Non-code files (JSON, Markdown, scripts, build artifacts) are not affected.

Allows:
  - Redirects to /dev/null
  - stderr redirects (2>, 2>&1)
  - File-descriptor redirects (>&1, >&2)
  - Read redirects (< file)
  - Any write that does not target a protected extension
"""

import json
import re
import sys

# Only block writes targeting these source code extensions.
_PROTECTED_EXTENSIONS = (".swift", ".kt", ".java")

# Patterns that indicate writing to a file via Bash.
# Each entry: (regex, human-readable name)
_WRITE_PATTERNS = [
    # tee — almost always writes to a file
    (r'\btee\b', "tee"),
    # heredoc redirect: cat << EOF > file  or  cat <<'EOF' > file
    (r"<<\s*['\"]?[A-Z_a-z]+['\"]?\s*>", "heredoc redirect"),
    # stdout redirect to a file path: > file or >> file
    # exclude: >/dev/null, >&N, 2>, N>
    (r"(?<![0-9&2])>{1,2}(?!&\d|/dev/null|\s*$)\s*\S", "output redirect (> or >>)"),
    # sed -i / sed -i'' / sed -i.bak — in-place file modification
    (r"\bsed\b.*\s-[a-zA-Z]*i", "sed in-place (-i)"),
    # perl -i / perl -pi — in-place file modification
    (r"\bperl\b.*\s-[a-zA-Z]*i", "perl in-place (-i)"),
    # python/python3 open(..., 'w') or open(..., 'a') — writing via Python one-liner
    (r"\bpython3?\b.*\bopen\s*\(.*['\"][wa]['\"]", "python open write"),
]

# Safe patterns — don't block even if a write pattern matched
_SAFE_PATTERNS = [
    r">{1,2}\s*/dev/null",   # redirect to /dev/null
    r">&\s*[0-9]",           # fd redirect >&1, >&2
    r"2>{1,2}",              # stderr redirect
]


def _targets_protected_file(command: str) -> bool:
    """Return True if the command string references a protected source extension."""
    return any(ext in command for ext in _PROTECTED_EXTENSIONS)


def _contains_file_write(command: str):
    """Return the matched pattern name if command writes to a protected file, else None."""
    if not _targets_protected_file(command):
        return None

    # Strip safe redirect patterns before checking write patterns
    for safe in _SAFE_PATTERNS:
        if re.search(safe, command):
            command = re.sub(safe, "", command)

    for pattern, name in _WRITE_PATTERNS:
        if re.search(pattern, command):
            return name
    return None


def _allow() -> None:
    sys.exit(0)


def _deny(reason: str) -> None:
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                f"[file-write-gate] Bash file write blocked ({reason}). "
                "Use the Write tool to create or modify files — "
                "this ensures the pre-write quality gate can review the content."
            ),
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

    if event.get("tool_name") != "Bash":
        _allow()
        return

    command = event.get("tool_input", {}).get("command", "")
    if not command:
        _allow()
        return

    match = _contains_file_write(command)
    if match:
        _deny(match)
    else:
        _allow()


if __name__ == "__main__":
    main()
