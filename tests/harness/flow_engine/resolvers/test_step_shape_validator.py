"""
solid-name: test_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests validating each step's field set against its declared type before content resolution or graph validation.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowValidationError
from harness.step_shape_validator import StepShapeValidator


class TestStepShapeValidator(unittest.TestCase):

    def setUp(self):
        self.sut = StepShapeValidator()

    def test_accepts_agent_step_with_only_prompt(self):
        self.sut.validate([{"id": "a", "type": "agent", "prompt": "p"}])

    def test_accepts_agent_step_with_only_prompt_file(self):
        self.sut.validate([{"id": "a", "type": "agent", "prompt_file": "p.md"}])

    def test_defaults_missing_type_to_agent(self):
        self.sut.validate([{"id": "a", "prompt": "p"}])

    def test_raises_when_agent_step_declares_both_prompt_and_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate([{"id": "a", "type": "agent", "prompt": "p", "prompt_file": "p.md"}])

    def test_raises_when_agent_step_declares_neither_prompt_nor_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate([{"id": "a", "type": "agent"}])

    def test_raises_when_agent_step_declares_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate([{"id": "a", "type": "agent", "prompt": "p", "command": ["ls"]}])

    def test_accepts_script_step_with_only_command(self):
        self.sut.validate([{"id": "a", "type": "script", "command": ["ls", "-la"]}])

    def test_raises_when_script_step_missing_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate([{"id": "a", "type": "script"}])

    def test_raises_when_script_step_declares_prompt(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate([{"id": "a", "type": "script", "command": ["ls"], "prompt": "p"}])

    def test_raises_when_script_step_declares_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate([{"id": "a", "type": "script", "command": ["ls"], "prompt_file": "p.md"}])


if __name__ == "__main__":
    unittest.main()
