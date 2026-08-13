"""
solid-name: test_command_allowlist_validator
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-035]
solid-description: Tests validating workflow process executables against a permitted-executable allowlist.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.models import FlowValidationError
from harness.step_declaration import StepDeclaration
from harness.step_executable_resolver import StepExecutableResolver


class TestCommandAllowlistValidator(unittest.TestCase):

    def setUp(self):
        self.sut = CommandAllowlistValidator(
            StepExecutableResolver(),
            FlowValidationErrorFactory(),
        )

    def test_accepts_command_naming_a_permitted_executable(self):
        self.sut.validate(
            [StepDeclaration(id="a", type="script", command=["python3", "run.py"])],
            allowlist=["python3"],
        )

    def test_ignores_agent_steps(self):
        self.sut.validate([StepDeclaration(id="a", type="agent", prompt="p")], allowlist=[])

    def test_accepts_structured_script_executor(self):
        self.sut.validate(
            [
                StepDeclaration(
                    id="a",
                    type="script",
                    script_file="/package/scripts/run.py",
                    executor="python3",
                )
            ],
            allowlist=["python3"],
        )

    def test_accepts_default_bash_executor_for_inline_command(self):
        self.sut.validate(
            [StepDeclaration(id="a", type="command", command="git status")],
            allowlist=["bash"],
        )

    def test_raises_when_inline_command_executor_is_not_permitted(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                [
                    StepDeclaration(
                        id="a",
                        type="command",
                        command="print('hello')",
                        executor="python3",
                    )
                ],
                allowlist=["bash"],
            )

    def test_raises_when_executable_not_on_allowlist(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                [StepDeclaration(id="a", type="script", command=["curl", "evil.example"])],
                allowlist=["python3"],
            )


if __name__ == "__main__":
    unittest.main()
