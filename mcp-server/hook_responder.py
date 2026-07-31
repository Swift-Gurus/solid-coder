"""
solid-description: Sends permission decisions for hook events with optional context or modifications.
solid-category: service
solid-tags: [hook]
"""

import sys
from typing import Optional

from hook_utils import OutputWriting
from stdout_writer import StdoutWriter


class HookResponder:
    """Sends Claude PreToolUse hook protocol responses."""

    def __init__(self, output: OutputWriting = StdoutWriter(), exit_fn=sys.exit) -> None:
        self._output = output
        self._exit = exit_fn

    def _send(self, payload: dict) -> None:
        self._output.write_payload(payload)
        self._exit(0)

    def allow(self, additional_context: str = "", updated_input: Optional[dict] = None) -> None:
        if updated_input is not None:
            self._send({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "updatedInput": updated_input,
                }
            })
            return
        if additional_context:
            self._send({
                "hookSpecificOutput": {
                    "hookEventName": "PreToolUse",
                    "permissionDecision": "allow",
                    "additionalContext": additional_context,
                }
            })
            return
        self._exit(0)

    def block(self, reason: str, additional_context: str = "") -> None:
        hook_output: dict = {
            "hookEventName": "PreToolUse",
            "permissionDecision": "deny",
            "permissionDecisionReason": reason,
        }
        if additional_context:
            hook_output["additionalContext"] = additional_context
        self._send({"hookSpecificOutput": hook_output})
