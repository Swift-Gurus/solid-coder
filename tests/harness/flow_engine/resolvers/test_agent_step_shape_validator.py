"""
solid-name: test_agent_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests validating the field set of an agent-type step.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.agent_step_shape_validator import AgentStepShapeValidator
from harness.models import FlowValidationError


class TestAgentStepShapeValidator(unittest.TestCase):

    def setUp(self):
        self.sut = AgentStepShapeValidator()

    def test_accepts_step_with_only_prompt(self):
        self.sut.validate({"id": "a", "type": "agent", "prompt": "p"})

    def test_accepts_step_with_only_prompt_file(self):
        self.sut.validate({"id": "a", "type": "agent", "prompt_file": "p.md"})

    def test_raises_when_declares_both_prompt_and_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "agent", "prompt": "p", "prompt_file": "p.md"})

    def test_raises_when_declares_neither_prompt_nor_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "agent"})

    def test_raises_when_declares_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "agent", "prompt": "p", "command": ["ls"]})


if __name__ == "__main__":
    unittest.main()
