"""
solid-name: test_process_execution_factory
solid-category: unit-test
solid-spec: [SPEC-027, SPEC-035]
solid-description: Tests translation of typed workflow-step objects into executable process requests.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.process_execution_factory import ProcessExecutionFactory
from harness.step_def import StepDef


class TestProcessExecutionFactory(unittest.TestCase):
    def setUp(self):
        self.sut = ProcessExecutionFactory(FlowValidationErrorFactory())

    def test_creates_script_file_arguments_without_shell_reconstruction(self):
        execution = self.sut.create(StepDef(
            id="validate",
            prompt="",
            type="script",
            script_file="/package/scripts/validate.py",
            executor="python3",
            args=["--strict"],
        ))

        self.assertEqual(
            execution.process_arguments(),
            ["python3", "/package/scripts/validate.py", "--strict"],
        )

    def test_defaults_script_file_executor_to_bash(self):
        execution = self.sut.create(StepDef(
            id="validate",
            prompt="",
            type="script",
            script_file="/package/scripts/validate.sh",
        ))

        self.assertEqual(
            execution.process_arguments(),
            ["bash", "/package/scripts/validate.sh"],
        )

    def test_creates_inline_command_as_one_shell_argument(self):
        execution = self.sut.create(StepDef(
            id="status",
            prompt="",
            type="command",
            command="git status --short",
        ))

        self.assertEqual(
            execution.process_arguments(),
            ["bash", "-lc", "git status --short"],
        )

    def test_preserves_legacy_script_argument_array(self):
        execution = self.sut.create(StepDef(
            id="legacy",
            prompt="",
            type="script",
            command=["python3", "validate.py"],
        ))

        self.assertEqual(
            execution.process_arguments(),
            ["python3", "validate.py"],
        )

    def test_rejects_non_process_step(self):
        with self.assertRaises(FlowValidationError):
            self.sut.create(StepDef(id="review", prompt="Review"))


if __name__ == "__main__":
    unittest.main()
