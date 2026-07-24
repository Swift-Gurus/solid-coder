"""
solid-name: test_delegate_step_shape_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests validating the field set of a delegate-type step.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.delegate_step_shape_validator import DelegateStepShapeValidator
from harness.models import FlowValidationError


class TestDelegateStepShapeValidator(unittest.TestCase):

    def setUp(self):
        self.sut = DelegateStepShapeValidator()

    def test_accepts_subagent_mode_with_prompt(self):
        self.sut.validate({"id": "a", "type": "delegate", "mode": "subagent", "prompt": "p"})

    def test_accepts_session_mode_with_prompt(self):
        self.sut.validate({"id": "a", "type": "delegate", "mode": "session", "prompt": "p"})

    def test_raises_when_missing_prompt(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "delegate", "mode": "subagent"})

    def test_raises_when_declares_command(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "delegate", "mode": "subagent", "prompt": "p", "command": ["ls"]})

    def test_raises_when_mode_missing(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "delegate", "prompt": "p"})

    def test_raises_when_mode_invalid(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate({"id": "a", "type": "delegate", "mode": "bogus", "prompt": "p"})


if __name__ == "__main__":
    unittest.main()
