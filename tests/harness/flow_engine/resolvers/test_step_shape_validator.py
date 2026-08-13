"""
solid-name: test_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests routing each step to the field-set validator registered for its declared type.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.step_declaration import StepDeclaration
from harness.step_field_validator_registration import StepFieldValidatorRegistration
from harness.step_shape_validator import StepShapeValidator


class _RecordingValidator:
    def __init__(self):
        self.seen = []

    def validate(self, step):
        self.seen.append(step)


class TestStepShapeValidator(unittest.TestCase):

    def setUp(self):
        self.agent_validator = _RecordingValidator()
        self.script_validator = _RecordingValidator()
        self.default_validator = _RecordingValidator()
        self.sut = StepShapeValidator(
            registrations=[
                StepFieldValidatorRegistration("agent", self.agent_validator),
                StepFieldValidatorRegistration("script", self.script_validator),
            ],
            default=self.default_validator,
        )

    def test_routes_step_to_validator_registered_for_its_type(self):
        step = StepDeclaration(id="a", type="script", command=["ls"])
        self.sut.validate([step])
        self.assertEqual(self.script_validator.seen, [step])
        self.assertEqual(self.agent_validator.seen, [])

    def test_defaults_missing_type_to_agent(self):
        step = StepDeclaration(id="a", prompt="p")
        self.sut.validate([step])
        self.assertEqual(self.agent_validator.seen, [step])

    def test_routes_unregistered_type_to_default_validator(self):
        step = StepDeclaration(id="a", type="mystery")
        self.sut.validate([step])
        self.assertEqual(self.default_validator.seen, [step])

    def test_routes_each_step_independently(self):
        steps = [
            StepDeclaration(id="a", type="agent", prompt="p"),
            StepDeclaration(id="b", type="script", command=["ls"]),
        ]
        self.sut.validate(steps)
        self.assertEqual(self.agent_validator.seen, [steps[0]])
        self.assertEqual(self.script_validator.seen, [steps[1]])


if __name__ == "__main__":
    unittest.main()
