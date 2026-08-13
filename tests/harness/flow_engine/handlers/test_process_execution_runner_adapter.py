"""
solid-name: test_process_execution_runner_adapter
solid-category: unit-test
solid-spec: [SPEC-035]
solid-description: Tests adaptation of typed process requests to the established argument-list subprocess boundary.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.inline_command_execution import InlineCommandExecution
from harness.process_execution_runner_adapter import ProcessExecutionRunnerAdapter
from harness.script_execution_result import ScriptExecutionResult


class StubArgumentRunner:
    def __init__(self, result: ScriptExecutionResult) -> None:
        self.result = result
        self.arguments = None
        self.timeout_seconds = None

    def run(self, arguments, timeout_seconds):
        self.arguments = arguments
        self.timeout_seconds = timeout_seconds
        return self.result


class TestProcessExecutionRunnerAdapter(unittest.TestCase):
    def test_materializes_arguments_only_at_subprocess_boundary(self):
        expected = ScriptExecutionResult(0, "clean", "", False)
        runner = StubArgumentRunner(expected)
        sut = ProcessExecutionRunnerAdapter(runner)
        execution = InlineCommandExecution("bash", "git status --short")

        result = sut.run(execution, 15)

        self.assertIs(result, expected)
        self.assertEqual(
            runner.arguments,
            ["bash", "-lc", "git status --short"],
        )
        self.assertEqual(runner.timeout_seconds, 15)


if __name__ == "__main__":
    unittest.main()
