"""
solid-name: test_script_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests validating the field set of a script-type step.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.models import FlowValidationError
from harness.script_step_shape_validator import ScriptStepShapeValidator


class TestScriptStepShapeValidator(unittest.TestCase):

    def setUp(self):
        self.sut = ScriptStepShapeValidator()

    def test_accepts_step_with_only_command(self):
        self.sut.validate({"id": "a", "type": "script", "command": ["ls", "-la"]})

    def test_raises_when_missing_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "script"})

    def test_raises_when_declares_prompt(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "script", "command": ["ls"], "prompt": "p"})

    def test_raises_when_declares_prompt_file(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "script", "command": ["ls"], "prompt_file": "p.md"})


if __name__ == "__main__":
    unittest.main()
