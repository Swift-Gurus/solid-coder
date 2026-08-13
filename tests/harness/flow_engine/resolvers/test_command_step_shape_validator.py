"""
solid-name: test_command_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Tests validation of inline-command workflow step declarations.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.command_step_shape_validator import CommandStepShapeValidator
from harness.command_step_value_validator import CommandStepValueValidator
from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.step_declaration import StepDeclaration


class TestCommandStepShapeValidator(unittest.TestCase):
    def setUp(self):
        error_factory = FlowValidationErrorFactory()
        self.sut = CommandStepShapeValidator(
            CommandStepValueValidator(error_factory),
            error_factory,
        )

    def test_accepts_inline_command_with_executor(self):
        self.sut.validate(
            StepDeclaration(
                id="status",
                type="command",
                command="git status --short",
                executor="bash",
            )
        )

    def test_raises_when_command_is_an_array(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(id="status", type="command", command=["git", "status"])
            )

    def test_raises_when_file_is_declared(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="status",
                    type="command",
                    command="git status",
                    script_file="/package/scripts/status.sh",
                )
            )

    def test_raises_when_arguments_are_declared(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="status",
                    type="command",
                    command="git status",
                    args=["--short"],
                )
            )

    def test_raises_when_executor_is_empty(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="status",
                    type="command",
                    command="git status",
                    executor="",
                )
            )


if __name__ == "__main__":
    unittest.main()
