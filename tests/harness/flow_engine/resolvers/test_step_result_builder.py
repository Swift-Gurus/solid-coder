"""
solid-name: test_step_result_builder
solid-category: unit-test
solid-spec: [SPEC-013, SPEC-027]
solid-description: Tests converting step instances to step results with resolved execution intent, attempts-remaining, and rejection reason.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, RunState, StepDef, StepInstance
from harness.step_result_builder import StepResultBuilder


class StubIntentResolver:
    def resolve(self, intent: str, detected_env: str) -> dict:
        return {"mode": intent}


class TestStepResultBuilder(unittest.TestCase):

    def setUp(self):
        self.sut = StepResultBuilder(intent_resolver=StubIntentResolver())

    def test_computes_attempts_remaining_from_max_attempts_and_attempts_used(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p", max_attempts=3)])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress", attempts_used={"a": 1})

        results = self.sut.build([instance], flow_def, "claude_code", run_state)

        self.assertEqual(results[0].attempts_remaining, 2)

    def test_reports_rejection_reason_for_reopened_step(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p")])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(
            completed={}, running=[], turn_count=0, status="in_progress",
            rejection_reasons={"a": "bad shape"},
        )

        results = self.sut.build([instance], flow_def, "claude_code", run_state)

        self.assertEqual(results[0].rejection_reason, "bad shape")

    def test_leaves_attempts_and_rejection_fields_none_when_untouched(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p", max_attempts=3)])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")

        results = self.sut.build([instance], flow_def, "claude_code", run_state)

        self.assertEqual(results[0].attempts_remaining, 3)
        self.assertIsNone(results[0].rejection_reason)


if __name__ == "__main__":
    unittest.main()
