"""
solid-name: test_step_builder
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests building executable StepDef instances from validated step declarations.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.step_builder import StepBuilder
from harness.step_declaration import StepDeclaration


class TestStepBuilder(unittest.TestCase):

    def setUp(self):
        self.sut = StepBuilder()

    def test_defaults_type_to_agent(self):
        step = self.sut.build(StepDeclaration(id="a", prompt="p"))
        self.assertEqual(step.type, "agent")

    def test_defaults_max_attempts_to_three_when_unset(self):
        step = self.sut.build(StepDeclaration(id="a", prompt="p"))
        self.assertEqual(step.max_attempts, 3)

    def test_reads_explicit_max_attempts(self):
        step = self.sut.build(StepDeclaration(id="a", prompt="p", max_attempts=5))
        self.assertEqual(step.max_attempts, 5)

    def test_reads_script_type_command_and_timeout(self):
        step = self.sut.build(
            StepDeclaration(
                id="a",
                type="script",
                command=["run.sh", "arg"],
                timeout_seconds=30,
            )
        )
        self.assertEqual(step.type, "script")
        self.assertEqual(step.command, ["run.sh", "arg"])
        self.assertEqual(step.timeout_seconds, 30)
        self.assertEqual(step.prompt, "")

    def test_reads_prompt_file_reference(self):
        step = self.sut.build(StepDeclaration(id="a", prompt_file="prompt.md"))
        self.assertEqual(step.prompt_file, "prompt.md")


if __name__ == "__main__":
    unittest.main()
