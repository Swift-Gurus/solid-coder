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

from hook_utils import GateHandling, make_hook_gate, parse_hook_event

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


class BashReadGate:
    """Detects Bash commands that read source files instead of using the Read tool.

    Blocks cat/head/tail when used with a source file argument.
    Allows: heredocs (cat <<'EOF'), pipeline targets (cmd | head), /dev/* paths.
    """

    _SOURCE_EXTENSIONS = (
        ".py", ".swift", ".kt", ".java", ".js", ".ts",
        ".json", ".md", ".toml", ".yaml", ".yml", ".sh",
    )

    _EXTERNAL_PREFIXES = ("/tmp/", "/var/", "/usr/", "/System/", "/Library/")

    def _looks_like_source_file(self, command: str) -> bool:
        if not any(ext in command for ext in self._SOURCE_EXTENSIONS):
            return False
        # Allow reads of files in temp/system directories (not project files)
        for token in command.split():
            if any(token.startswith(p) for p in self._EXTERNAL_PREFIXES):
                return False
        return True

    def _is_heredoc(self, command: str) -> bool:
        return "<<" in command

    def _is_devnull_or_special(self, command: str) -> bool:
        return "/dev/" in command

    def _is_pipeline_target(self, command: str, cmd_name: str) -> bool:
        return bool(re.search(rf"\|\s*{cmd_name}\b", command))

    def check(self, command: str) -> Optional[str]:
        """Return the read-command name if it reads a source file, else None."""
        if not self._looks_like_source_file(command):
            return None
        if self._is_heredoc(command) or self._is_devnull_or_special(command):
            return None
        for cmd_name in ("cat", "head", "tail"):
            if not re.search(rf"\b{cmd_name}\b", command):
                continue
            if self._is_pipeline_target(command, cmd_name):
                continue
            return cmd_name
        return None


class BashGateCoordinator:
    """Runs all Bash gate checks in order and issues the appropriate decision."""

    def __init__(
        self,
        chunk_gate: CommandChecking,
        read_gate: CommandChecking,
        write_gate: CommandChecking,
        gate: GateHandling,
    ) -> None:
        self._chunk = chunk_gate
        self._read = read_gate
        self._write = write_gate
        self._gate = gate

    def run(self, tool_name: str, command: str) -> None:
        if tool_name != "Bash" or not command:
            self._gate.allow()
            return

        if msg := self._chunk.check(command):
            self._gate.block(msg)
            return

        if name := self._read.check(command):
            self._gate.block(
                f"[file-read-gate] Bash file read blocked ({name}). "
                "Use the Read tool instead — it provides proper content with line numbers "
                "and ensures consistent access through the quality pipeline."
            )
            return

        if name := self._write.check(command):
            self._gate.block(
                f"[file-write-gate] Bash file write blocked ({name}). "
                "Use the Write tool to create or modify files — "
                "this ensures the pre-write quality gate can review the content."
            )
        else:
            self._gate.allow()


_coordinator = BashGateCoordinator(
    chunk_gate=ChunkReadGate(),
    read_gate=BashReadGate(),
    write_gate=BashWriteGate(),
    gate=_gate,
)


def main() -> None:
    parsed = parse_hook_event(sys.stdin.read())
    if parsed is None:
        _gate.allow()
        return
    tool_name, tool_input, _, _ = parsed
    _coordinator.run(tool_name, tool_input.get("command", ""))


if __name__ == "__main__":
    main()
