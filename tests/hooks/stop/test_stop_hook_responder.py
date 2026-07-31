"""
solid-name: test_stop_hook_responder
solid-category: unit-test
solid-description: Verifies StopHookResponder's response payloads and exit codes for different stop hook decisions.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[3] / "mcp-server"))

from stop_hook_responder import StopHookResponder


class RecordingOutput:
    def __init__(self) -> None:
        self.payloads = []

    def write_payload(self, payload: dict) -> None:
        self.payloads.append(payload)


def _build():
    output = RecordingOutput()
    exit_calls = []
    responder = StopHookResponder(output=output, exit_fn=exit_calls.append)
    return responder, output, exit_calls


class TestStopHookResponder(unittest.TestCase):
    def test_allow_writes_nothing_and_exits_zero(self):
        responder, output, exit_calls = _build()

        responder.allow()

        self.assertEqual(output.payloads, [])
        self.assertEqual(exit_calls, [0])

    def test_allow_with_context_writes_hook_specific_output_and_exits_zero(self):
        responder, output, exit_calls = _build()

        responder.allow(additional_context="reminder text")

        self.assertEqual(output.payloads, [{
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": "reminder text",
            }
        }])
        self.assertEqual(exit_calls, [0])

    def test_allow_ignores_updated_input_since_stop_events_have_no_tool_input(self):
        responder, output, exit_calls = _build()

        responder.allow(updated_input={"file_path": "/tmp/x"})

        self.assertEqual(output.payloads, [])
        self.assertEqual(exit_calls, [0])

    def test_block_writes_flat_decision_payload(self):
        responder, output, exit_calls = _build()

        responder.block("flow left in_progress")

        self.assertEqual(output.payloads, [{"decision": "block", "reason": "flow left in_progress"}])
        self.assertEqual(exit_calls, [0])

    def test_block_with_additional_context_includes_hook_specific_output(self):
        responder, output, exit_calls = _build()

        responder.block("flow left in_progress", additional_context="call flow_next")

        self.assertEqual(output.payloads, [{
            "decision": "block",
            "reason": "flow left in_progress",
            "hookSpecificOutput": {
                "hookEventName": "Stop",
                "additionalContext": "call flow_next",
            },
        }])
        self.assertEqual(exit_calls, [0])


if __name__ == "__main__":
    unittest.main()
