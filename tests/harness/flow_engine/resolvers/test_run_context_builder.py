"""
solid-name: test_run_context_builder
solid-category: unit-test
solid-spec: [SPEC-031, SPEC-027]
solid-description: Tests building the template interpolation context from run params, completed step outputs, rejection reasons, and attempts used.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import RunState, StepOutputs
from harness.run_context_builder import RunContextBuilder
from harness.step_outputs_builder import StepOutputsBuilder


class TestRunContextBuilder(unittest.TestCase):

    def setUp(self):
        self.sut = RunContextBuilder()

    def test_builds_context_with_params_and_completed_step_outputs(self):
        run_state = RunState(
            completed={"a": StepOutputsBuilder().build({"x": 1})},
            running=[],
            turn_count=0,
            status="in_progress",
        )

        context = self.sut.build({"key": "value"}, run_state)

        self.assertEqual(context["params"], {"key": "value"})
        self.assertEqual(context["steps"]["a"].get("x"), 1)

    def test_exposes_rejection_reasons_for_prompt_interpolation(self):
        run_state = RunState(
            completed={}, running=[], turn_count=1, status="in_progress",
            rejection_reasons={"writer": "bad shape"},
        )

        context = self.sut.build({}, run_state)

        self.assertEqual(context["rejection_reasons"], {"writer": "bad shape"})

    def test_exposes_attempts_used(self):
        run_state = RunState(
            completed={}, running=[], turn_count=1, status="in_progress",
            attempts_used={"writer": 2},
        )

        context = self.sut.build({}, run_state)

        self.assertEqual(context["attempts_used"], {"writer": 2})


if __name__ == "__main__":
    unittest.main()
