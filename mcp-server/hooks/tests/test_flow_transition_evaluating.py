"""
solid-name: test_flow_transition_evaluating
solid-category: unit-test
solid-description: Tests deciding whether a flow run may be left with a pending step at turn end.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from flow_transition_evaluating import FlowTransitionGate  # noqa: E402
from harness.flow_next_result import FlowNextResult  # noqa: E402
from harness.flow_status_result import FlowStatusResult  # noqa: E402


class StubStatusReader:
    def __init__(self, result: FlowStatusResult) -> None:
        self._result = result
        self.calls: list = []

    def flow_status(self, run_id=None) -> FlowStatusResult:
        self.calls.append(run_id)
        return self._result


class StubFailureRecorder:
    def __init__(self, terminal: FlowNextResult | None = None) -> None:
        self._terminal = terminal
        self.calls: list = []

    def record(self, run_id, step_id):
        self.calls.append((run_id, step_id))
        return self._terminal


def _status(status: str, pending=None, flow="test_flow", run_id="run-1") -> FlowStatusResult:
    return FlowStatusResult(
        flow=flow, run_id=run_id, status=status, turn_count=1, max_turns=10,
        completed=[], running=[], pending=pending or [],
    )


class TestFlowTransitionGate(unittest.TestCase):

    def test_allows_when_no_active_run(self):
        reader = StubStatusReader(_status("no_active_run"))
        recorder = StubFailureRecorder()
        sut = FlowTransitionGate(status_reader=reader, failure_recorder=recorder)

        self.assertEqual(sut.evaluate(), {"allow": True})
        self.assertEqual(recorder.calls, [])

    def test_allows_when_status_is_not_in_progress(self):
        reader = StubStatusReader(_status("done"))
        recorder = StubFailureRecorder()
        sut = FlowTransitionGate(status_reader=reader, failure_recorder=recorder)

        self.assertEqual(sut.evaluate(), {"allow": True})
        self.assertEqual(recorder.calls, [])

    def test_allows_when_in_progress_with_nothing_pending(self):
        reader = StubStatusReader(_status("in_progress", pending=[]))
        recorder = StubFailureRecorder()
        sut = FlowTransitionGate(status_reader=reader, failure_recorder=recorder)

        self.assertEqual(sut.evaluate(), {"allow": True})
        self.assertEqual(recorder.calls, [])

    def test_blocks_and_records_a_failed_attempt_when_a_step_is_pending(self):
        reader = StubStatusReader(_status("in_progress", pending=["step-a"], flow="code_review", run_id="run-42"))
        recorder = StubFailureRecorder(terminal=None)
        sut = FlowTransitionGate(status_reader=reader, failure_recorder=recorder)

        result = sut.evaluate()

        self.assertFalse(result["allow"])
        self.assertIn("code_review", result["reason"])
        self.assertIn("run-42", result["reason"])
        self.assertIn("step-a", result["reason"])
        self.assertEqual(recorder.calls, [(None, "step-a")])

    def test_uses_the_terminal_error_message_when_the_step_exhausts_its_attempts(self):
        reader = StubStatusReader(_status("in_progress", pending=["step-a"]))
        terminal = FlowNextResult(status="failed", error="Flow failed — step 'step-a' exhausted all 3 attempt(s).")
        recorder = StubFailureRecorder(terminal=terminal)
        sut = FlowTransitionGate(status_reader=reader, failure_recorder=recorder)

        result = sut.evaluate()

        self.assertEqual(result, {"allow": False, "reason": terminal.error})

    def test_forwards_run_id_to_the_status_reader_and_failure_recorder(self):
        reader = StubStatusReader(_status("in_progress", pending=["step-a"]))
        recorder = StubFailureRecorder(terminal=None)
        sut = FlowTransitionGate(status_reader=reader, failure_recorder=recorder)

        sut.evaluate(run_id="isolated-run-1")

        self.assertEqual(reader.calls, ["isolated-run-1"])
        self.assertEqual(recorder.calls, [("isolated-run-1", "step-a")])


if __name__ == "__main__":
    unittest.main()
