"""
solid-name: test_agent_step_handler
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests that agent steps always signal awaiting input on run and delegate validation to the existing output validator.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.agent_step_handler import AgentStepHandler
from harness.models import FlowDef, StepDef, StepInstance


class StubOutputValidator:
    def __init__(self, errors: list[str]) -> None:
        self._errors = errors
        self.calls: list[tuple] = []

    def validate(self, ready, outputs, flow_def) -> list[str]:
        self.calls.append((ready, outputs, flow_def))
        return self._errors


class TestAgentStepHandler(unittest.TestCase):

    def test_run_always_signals_awaiting_input(self):
        sut = AgentStepHandler(output_validator=StubOutputValidator([]))
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")

        outcome = sut.run(instance, StepDef(id="a", prompt="p"))

        self.assertTrue(outcome.awaiting_input)
        self.assertIsNone(outcome.outputs)

    def test_validate_delegates_to_existing_output_validator_for_the_single_instance(self):
        validator = StubOutputValidator([])
        sut = AgentStepHandler(output_validator=validator)
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")
        flow_def = FlowDef(name="f", max_turns=10, steps=[])

        result = sut.validate(instance, {"x": 1}, flow_def)

        self.assertTrue(result.ok)
        self.assertEqual(validator.calls, [([instance], {"a-1": {"x": 1}}, flow_def)])

    def test_validate_reports_errors_from_output_validator(self):
        validator = StubOutputValidator(["missing field"])
        sut = AgentStepHandler(output_validator=validator)
        instance = StepInstance(step_id="a", instance_id="a-1", item=None, prompt="p")

        result = sut.validate(instance, {}, FlowDef(name="f", max_turns=10, steps=[]))

        self.assertFalse(result.ok)
        self.assertEqual(result.errors, ["missing field"])


if __name__ == "__main__":
    unittest.main()
