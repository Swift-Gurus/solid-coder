"""
solid-description: Responds to Stop hook events with allow or block decisions.
solid-category: service
solid-tags: [hook]
"""

import sys
from typing import Optional

from hook_responding import HookResponding
from hook_utils import OutputWriting
from stdout_writer import StdoutWriter


class StopHookResponder(HookResponding):
    """Sends Claude Stop/SubagentStop hook protocol responses — flat decision/reason,
    unlike PreToolUse's nested hookSpecificOutput (see HookResponder). Stop events carry
    no tool_input, so updated_input is always ignored."""

    def __init__(self, output: OutputWriting = StdoutWriter(), exit_fn=sys.exit) -> None:
        self._output = output
        self._exit = exit_fn

    def allow(self, additional_context: str = "", updated_input: Optional[dict] = None) -> None:
        if additional_context:
            self._output.write_payload({
                "hookSpecificOutput": {
                    "hookEventName": "Stop",
                    "additionalContext": additional_context,
                }
            })
        self._exit(0)

    def block(self, reason: str, additional_context: str = "") -> None:
        payload: dict = {"decision": "block", "reason": reason}
        if additional_context:
            payload["hookSpecificOutput"] = {
                "hookEventName": "Stop",
                "additionalContext": additional_context,
            }
        self._output.write_payload(payload)
        self._exit(0)
