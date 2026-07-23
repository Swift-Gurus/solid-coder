"""
solid-name: test_command_allowlist_validator
solid-category: unit-test
solid-spec: [SPEC-027]
solid-description: Tests validating script step commands against a permitted-executable allowlist at load time.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.command_allowlist_validator import CommandAllowlistValidator
from harness.models import FlowValidationError


class TestCommandAllowlistValidator(unittest.TestCase):

    def setUp(self):
        self.sut = CommandAllowlistValidator()

    def test_accepts_command_naming_a_permitted_executable(self):
        self.sut.validate(
            [{"id": "a", "type": "script", "command": ["python3", "run.py"]}],
            allowlist=["python3"],
        )

    def test_ignores_agent_steps(self):
        self.sut.validate([{"id": "a", "type": "agent", "prompt": "p"}], allowlist=[])

    def test_raises_when_executable_not_on_allowlist(self):
        with self.assertRaises(FlowValidationError):
            self.sut.validate(
                [{"id": "a", "type": "script", "command": ["curl", "evil.example"]}],
                allowlist=["python3"],
            )


if __name__ == "__main__":
    unittest.main()
