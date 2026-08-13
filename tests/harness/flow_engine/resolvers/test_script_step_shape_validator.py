"""
solid-name: test_script_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-035]
solid-description: Tests validating structured and compatible legacy script-step declarations.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.models import FlowValidationError
from harness.script_step_shape_validator import ScriptStepShapeValidator
from harness.script_step_value_validator import ScriptStepValueValidator
from harness.step_declaration import StepDeclaration


class TestScriptStepShapeValidator(unittest.TestCase):

    def setUp(self):
        error_factory = FlowValidationErrorFactory()
        self.sut = ScriptStepShapeValidator(
            ScriptStepValueValidator(error_factory),
            error_factory,
        )

    def test_accepts_step_with_only_command(self):
        self.sut.validate(
            StepDeclaration(id="a", type="script", command=["ls", "-la"])
        )

    def test_accepts_resolved_script_file_with_executor_and_arguments(self):
        self.sut.validate(
            StepDeclaration(
                id="a",
                type="script",
                script_file="/package/scripts/check.py",
                executor="python3",
                args=["--strict"],
            )
        )

    def test_raises_when_missing_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(StepDeclaration(id="a", type="script"))

    def test_raises_when_declares_prompt(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(id="a", type="script", command=["ls"], prompt="p")
            )

    def test_raises_when_declares_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="a",
                    type="script",
                    command=["ls"],
                    prompt_file="p.md",
                )
            )

    def test_raises_when_script_file_is_mixed_with_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="a",
                    type="script",
                    script_file="/package/scripts/check.py",
                    command=["python3", "check.py"],
                )
            )

    def test_raises_when_legacy_command_is_scalar(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(id="a", type="script", command="python3 check.py")
            )

    def test_raises_when_script_arguments_are_not_strings(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="a",
                    type="script",
                    script_file="/package/scripts/check.py",
                    args=[1],
                )
            )

    def test_raises_when_legacy_command_has_structured_executor(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                StepDeclaration(
                    id="a",
                    type="script",
                    command=["python3", "check.py"],
                    executor="python3",
                )
            )


if __name__ == "__main__":
    unittest.main()
