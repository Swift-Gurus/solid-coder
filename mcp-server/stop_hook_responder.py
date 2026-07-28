"""
solid-description: Responds to hook events with allow or block decisions.
solid-category: service
solid-tags: [hook]
"""

import sys

from hook_utils import OutputWriting
from simple_hook_responding import SimpleHookResponding
from stdout_writer import StdoutWriter


class StopHookResponder(SimpleHookResponding):
    """Sends Claude Stop/SubagentStop hook protocol responses — flat decision/reason,
    unlike PreToolUse's nested hookSpecificOutput (see HookResponder)."""

    def __init__(self, output: OutputWriting = StdoutWriter(), exit_fn=sys.exit) -> None:
        self._output = output
        self._exit = exit_fn

    def allow(self) -> None:
        self._exit(0)

    def block(self, reason: str, additional_context: str = "") -> None:
        self._output.write_payload({"decision": "block", "reason": reason})
        self._exit(0)
