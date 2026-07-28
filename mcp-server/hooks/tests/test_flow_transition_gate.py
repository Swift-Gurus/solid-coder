"""
solid-name: test_flow_transition_gate
solid-category: unit-test
solid-description: Tests the Stop-hook script that blocks the main session from ending its turn on an in_progress flow.
"""

import io
import json
import sys
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flow_transition_gate import main  # noqa: E402


class StubGate:
    def __init__(self, result: dict) -> None:
        self._result = result
        self.evaluate_calls = 0

    def evaluate(self) -> dict:
        self.evaluate_calls += 1
        return self._result


def _run(event: dict, gate: StubGate) -> tuple:
    raw = json.dumps(event)
    out = io.StringIO()
    exit_code = None
    with patch("sys.stdin", io.StringIO(raw)):
        with redirect_stdout(out):
            try:
                main(gate=gate)
            except SystemExit as e:
                exit_code = e.code
    return exit_code, out.getvalue()


class TestFlowTransitionGate(unittest.TestCase):
    """The responder always exits(0) — allow vs. block is distinguished by whether a
    {"decision": "block", ...} JSON payload was written to stdout, not by exit code."""

    def test_allows_and_never_evaluates_when_stop_hook_already_active(self):
        gate = StubGate({"allow": False, "reason": "should never be seen"})

        exit_code, stdout = _run({"stop_hook_active": True}, gate)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "")
        self.assertEqual(gate.evaluate_calls, 0)

    def test_allows_on_invalid_json_stdin(self):
        gate = StubGate({"allow": False, "reason": "should never be seen"})
        out = io.StringIO()
        exit_code = None
        with patch("sys.stdin", io.StringIO("not json")):
            with redirect_stdout(out):
                try:
                    main(gate=gate)
                except SystemExit as e:
                    exit_code = e.code

        self.assertEqual(exit_code, 0)
        self.assertEqual(out.getvalue(), "")
        self.assertEqual(gate.evaluate_calls, 0)

    def test_allows_when_gate_reports_allow(self):
        gate = StubGate({"allow": True})

        exit_code, stdout = _run({}, gate)

        self.assertEqual(exit_code, 0)
        self.assertEqual(stdout, "")

    def test_blocks_with_reason_as_json_on_stdout(self):
        gate = StubGate({"allow": False, "reason": "Flow 'x' has pending step(s) ['a']."})

        exit_code, stdout = _run({}, gate)

        self.assertEqual(exit_code, 0)
        self.assertEqual(
            json.loads(stdout),
            {"decision": "block", "reason": "Flow 'x' has pending step(s) ['a']."},
        )


if __name__ == "__main__":
    unittest.main()
