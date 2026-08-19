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
class StubArgumentRunner:
    def __init__(self) -> None:
        self.arguments = None
        self.timeout_seconds = None
        self.working_directory = None

    def run(self, arguments, timeout=None, cwd=None):
        self.arguments = arguments
        self.timeout_seconds = timeout
        self.working_directory = cwd
        return True, "clean", ""


class TestProcessExecutionRunnerAdapter(unittest.TestCase):
    def test_materializes_arguments_only_at_subprocess_boundary(self):
        runner = StubArgumentRunner()
        sut = ProcessExecutionRunnerAdapter(runner)
        execution = InlineCommandExecution("bash", "git status --short")

        result = sut.run(execution, 15, "/project")

        self.assertEqual(result.exit_code, 0)
        self.assertEqual(result.stdout, "clean")
        self.assertEqual(result.stderr, "")
        self.assertFalse(result.timed_out)
        self.assertEqual(
            runner.arguments,
            ["bash", "-lc", "git status --short"],
        )
        self.assertEqual(runner.timeout_seconds, 15)
        self.assertEqual(runner.working_directory, "/project")


if __name__ == "__main__":
    unittest.main()
