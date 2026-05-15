#!/usr/bin/env python3
"""PreToolUse hook — block Bash writes to source code files and reads of MCP chunk files.

Prevents agents from using Bash to:
  1. Write or modify source code files (sed -i, perl -pi, tee, redirects, etc.).
     Source code changes must go through the Write or Edit tools so the
     pre-write quality gate can review.
  2. Read MCP chunk files. When an MCP tool returns content too large to fit
     in a single response, it writes numbered chunk files prefixed with
     "solid-coder-" and instructs the agent to read them with the Read tool.
     Using Bash (cat, head, tail, etc.) skips or truncates chunks — use the
     Read tool instead.

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
from typing import Tuple

# Only block writes targeting these source code extensions.
_PROTECTED_EXTENSIONS = (".swift", ".kt", ".java")

# Patterns that indicate writing to a file via Bash.
# Each entry: (regex, re_flags, human-readable name)
_WRITE_PATTERNS: list[Tuple[str, int, str]] = [
    # tee — almost always writes to a file
    (r'\btee\b', 0, "tee"),
    # heredoc redirect: cat << EOF > file  or  cat <<'EOF' > file
    (r"<<\s*['\"]?[A-Z_a-z]+['\"]?\s*>", 0, "heredoc redirect"),
    # stdout redirect to a file path: > file or >> file
    # exclude: >/dev/null, >&N, 2>, N>
    (r"(?<![0-9&2])>{1,2}(?!&\d|/dev/null|\s*$)\s*\S", 0, "output redirect (> or >>)"),
    # sed -i / sed -i'' / sed -i.bak — in-place file modification
    (r"\bsed\b.*\s-[a-zA-Z]*i", 0, "sed in-place (-i)"),
    # perl -i / perl -pi — in-place file modification
    (r"\bperl\b.*\s-[a-zA-Z]*i", 0, "perl in-place (-i)"),
    # python/python3 open(..., 'w') or open(..., 'a') — writing via Python one-liner or
    # multi-line -c block. re.DOTALL lets .* span newlines so the python3 keyword and
    # the open() call don't have to appear on the same line.
    (r"\bpython3?\b.*\bopen\s*\(.*['\"][wa]['\"]", re.DOTALL, "python open write"),
]

# Safe patterns — don't block even if a write pattern matched
_SAFE_PATTERNS = [
    r">{1,2}\s*/dev/null",   # redirect to /dev/null
    r">&\s*[0-9]",           # fd redirect >&1, >&2
    r"2>{1,2}",              # stderr redirect
]


# Chunk files written by the MCP docs server when a payload exceeds _CHUNK_SIZE.
# Named: solid-coder-{prefix}-{timestamp}-{n}of{total}.md
# tempfile.gettempdir() varies by OS (/tmp on Linux, /var/folders/.../T on macOS),
# so we match on the filename prefix only.
_CHUNK_FILE_PREFIX = "solid-coder-"


def _reads_chunk_file(command: str) -> bool:
    """Return True if the command accesses an MCP chunk file via Bash."""
    return _CHUNK_FILE_PREFIX in command


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

    for pattern, flags, name in _WRITE_PATTERNS:
        if re.search(pattern, command, flags):
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


def _deny_chunk_read() -> None:
    sys.stdout.write(json.dumps({
        "hookSpecificOutput": {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": (
                "[chunk-read-gate] MCP chunk files must be read with the Read tool, not Bash. "
                "The MCP returned multiple chunk paths and instructed you to read each one "
                "in order using the Read tool. Using Bash (cat, head, tail, etc.) truncates "
                "or skips chunks. Use the Read tool on each path listed in the MCP response."
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

    if _reads_chunk_file(command):
        _deny_chunk_read()

    match = _contains_file_write(command)
    if match:
        _deny(match)
    else:
        _allow()


if __name__ == "__main__":
    main()
