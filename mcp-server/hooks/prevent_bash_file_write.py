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

import sys
from pathlib import Path
from typing import Optional, Protocol

_MCP_DIR = Path(__file__).resolve().parents[1]
if str(_MCP_DIR) not in sys.path:
    sys.path.insert(0, str(_MCP_DIR))

from hook_utils import GateHandling, HookGateFactory, parse_hook_event
from chunk_read_gate import ChunkReadGate
from bash_write_gate import BashWriteGate
from bash_read_gate import BashReadGate

_gate = HookGateFactory().build()


class CommandChecking(Protocol):
    def check(self, command: str) -> Optional[str]: ...


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


def main(
    coordinator: BashGateCoordinator = _coordinator,
    gate: GateHandling = _gate,
) -> None:
    parsed = parse_hook_event(sys.stdin.read())
    if parsed is None:
        gate.allow()
        return
    tool_name, tool_input, _, _, _ = parsed
    coordinator.run(tool_name, tool_input.get("command", ""))


if __name__ == "__main__":
    main()
