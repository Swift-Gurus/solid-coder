"""
solid-name: test_flow_start_result_builder
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests assembling a FlowStartResult from a run's execution outcome.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.execution_outcome import ExecutionOutcome
from harness.flow_next_result import FlowNextResult
from harness.flow_start_result_builder import FlowStartResultBuilder
from harness.step_result import StepResult


class TestFlowStartResultBuilder(unittest.TestCase):

    def setUp(self):
        self.sut = FlowStartResultBuilder()

    def test_builds_a_ready_result_with_the_outcomes_steps_when_not_isolated(self):
        step = StepResult(step_id="a", instance_id="a-1", prompt="Do a", execution={"mode": "inline"})

        result = self.sut.build("run-1", ExecutionOutcome(steps=[step]), isolated=False)

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [step])
        self.assertIsNone(result.error)
        self.assertIsNone(result.status)
        self.assertFalse(result.isolated)

    def test_marks_the_result_isolated_when_requested(self):
        result = self.sut.build("run-1", ExecutionOutcome(steps=[]), isolated=True)

        self.assertTrue(result.isolated)

    def test_builds_an_error_result_when_the_outcome_has_an_interpolation_error(self):
        result = self.sut.build("run-1", ExecutionOutcome(error="bad reference"), isolated=False)

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [])
        self.assertEqual(result.error, "bad reference")
        self.assertIsNone(result.status)

    def test_builds_a_terminal_result_carrying_the_terminals_error_and_status(self):
        terminal = FlowNextResult(status="failed", error="Flow failed — step 'a' exhausted all 2 attempt(s).")

        result = self.sut.build("run-1", ExecutionOutcome(terminal=terminal), isolated=False)

        self.assertEqual(result.run_id, "run-1")
        self.assertEqual(result.steps, [])
        self.assertEqual(result.error, "Flow failed — step 'a' exhausted all 2 attempt(s).")
        self.assertEqual(result.status, "failed")

    def test_builds_a_done_terminal_result_with_no_error_but_a_status(self):
        terminal = FlowNextResult(status="done")

        result = self.sut.build("run-1", ExecutionOutcome(terminal=terminal), isolated=False)

        self.assertIsNone(result.error)
        self.assertEqual(result.status, "done")

    def test_an_error_takes_precedence_over_a_terminal_if_somehow_both_are_set(self):
        terminal = FlowNextResult(status="failed", error="terminal error")

        result = self.sut.build(
            "run-1", ExecutionOutcome(error="interpolation error", terminal=terminal), isolated=False
        )

        self.assertEqual(result.error, "interpolation error")
        self.assertIsNone(result.status)


if __name__ == "__main__":
    unittest.main()
