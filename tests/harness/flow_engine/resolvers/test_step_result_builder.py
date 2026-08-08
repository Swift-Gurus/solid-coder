"""
solid-name: test_step_result_builder
solid-category: unit-test
solid-spec: [SPEC-031, SPEC-027]
solid-description: Tests converting step instances to step results with resolved execution mode and rejection reason.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowDef, RunState, StepDef, StepInstance
from harness.step_result_builder import StepResultBuilder


class TestStepResultBuilder(unittest.TestCase):

    def setUp(self):
        self.sut = StepResultBuilder()

    def test_reports_rejection_reason_for_reopened_step(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p")])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(
            completed={}, running=[], turn_count=0, status="in_progress",
            rejection_reasons={"a": "bad shape"},
        )

        results = self.sut.build([instance], flow_def, run_state)

        self.assertEqual(results[0].rejection_reason, "bad shape")

    def test_leaves_rejection_reason_none_when_untouched(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p", max_attempts=3)])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        run_state = RunState(completed={}, running=[], turn_count=0, status="in_progress")

        results = self.sut.build([instance], flow_def, run_state)

        self.assertIsNone(results[0].rejection_reason)

    def test_agent_step_resolves_to_inline_execution_mode(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="p", type="agent")])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")

        results = self.sut.build([instance], flow_def)

        self.assertEqual(results[0].execution, {"mode": "inline"})

    def test_script_step_resolves_to_inline_execution_mode(self):
        flow_def = FlowDef(name="f", max_turns=10, steps=[StepDef(id="a", prompt="", type="script", command=["ls"])])
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="")

        results = self.sut.build([instance], flow_def)

        self.assertEqual(results[0].execution, {"mode": "inline"})

    def test_delegate_step_resolves_execution_mode_from_its_declared_mode(self):
        flow_def = FlowDef(
            name="f", max_turns=10,
            steps=[StepDef(id="a", prompt="p", type="delegate", mode="subagent")],
        )
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")

        results = self.sut.build([instance], flow_def)

        self.assertEqual(results[0].execution, {"mode": "subagent"})

    def test_delegate_step_with_session_mode_resolves_accordingly(self):
        flow_def = FlowDef(
            name="f", max_turns=10,
            steps=[StepDef(id="a", prompt="p", type="delegate", mode="session")],
        )
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")

        results = self.sut.build([instance], flow_def)

        self.assertEqual(results[0].execution, {"mode": "session"})


if __name__ == "__main__":
    unittest.main()
