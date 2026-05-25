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

import re
import sys
from pathlib import Path
from typing import Optional, Protocol, Tuple

_HOOKS_DIR = Path(__file__).resolve().parent
if str(_HOOKS_DIR) not in sys.path:
    sys.path.insert(0, str(_HOOKS_DIR))

from hook_utils import make_hook_gate, parse_hook_event

_gate = make_hook_gate()


class CommandChecking(Protocol):
    def check(self, command: str) -> Optional[str]: ...


class ChunkReadGate:
    """Detects Bash commands that read MCP chunk files instead of using the Read tool."""

    # Chunk files are named: solid-coder-{prefix}-{timestamp}-{n}of{total}.md
    _CHUNK_RE = re.compile(r'solid-coder-\S+-\d+-\d+of\d+\.md')
    _MSG = (
        "[chunk-read-gate] MCP chunk files must be read with the Read tool, not Bash. "
        "The MCP returned multiple chunk paths and instructed you to read each one "
        "in order using the Read tool. Using Bash (cat, head, tail, etc.) truncates "
        "or skips chunks. Use the Read tool on each path listed in the MCP response."
    )

    def check(self, command: str) -> Optional[str]:
        """Return the block message if command references an MCP chunk file, else None."""
        return self._MSG if self._CHUNK_RE.search(command) else None


class BashWriteGate:
    """Detects Bash commands that write to protected source-code file extensions."""

    _PROTECTED = (".swift", ".kt", ".java")

    _WRITE_PATTERNS: list[Tuple[str, int, str]] = [
        (r'\btee\b', 0, "tee"),
        (r"<<\s*['\"]?[A-Z_a-z]+['\"]?\s*>", 0, "heredoc redirect"),
        (r"(?<![0-9&2])>{1,2}(?!&\d|/dev/null|\s*$)\s*\S", 0, "output redirect (> or >>)"),
        (r"\bsed\b.*\s-[a-zA-Z]*i", 0, "sed in-place (-i)"),
        (r"\bperl\b.*\s-[a-zA-Z]*i", 0, "perl in-place (-i)"),
        (r"\bpython3?\b.*\bopen\s*\(.*['\"][wa][bt+]{0,3}['\"]", re.DOTALL, "python open write"),
    ]

    _SAFE_PATTERNS = [
        r">{1,2}\s*/dev/null",
        r">&\s*[0-9]",
        r"2>{1,2}",
    ]

    def _targets_protected_file(self, command: str) -> bool:
        return any(ext in command for ext in self._PROTECTED)

    def check(self, command: str) -> Optional[str]:
        """Return the matched write-pattern name if command writes to a protected file, else None."""
        if not self._targets_protected_file(command):
            return None
        sanitized = command
        for safe in self._SAFE_PATTERNS:
            if re.search(safe, sanitized):
                sanitized = re.sub(safe, "", sanitized)
        for pattern, flags, name in self._WRITE_PATTERNS:
            if re.search(pattern, sanitized, flags):
                return name
        return None


_chunk_gate: CommandChecking = ChunkReadGate()
_write_gate: CommandChecking = BashWriteGate()


def main() -> None:
    parsed = parse_hook_event(sys.stdin.read())
    if parsed is None:
        _gate.allow()
        return

    tool_name, tool_input, _, _ = parsed
    if tool_name != "Bash":
        _gate.allow()
        return

    command = tool_input.get("command", "")
    if not command:
        _gate.allow()
        return

    if msg := _chunk_gate.check(command):
        _gate.block(msg)
        return

    if name := _write_gate.check(command):
        _gate.block(
            f"[file-write-gate] Bash file write blocked ({name}). "
            "Use the Write tool to create or modify files — "
            "this ensures the pre-write quality gate can review the content."
        )
    else:
        _gate.allow()


if __name__ == "__main__":
    main()
