"""
solid-name: test_subagent_delegator
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests wrapping a step's body with a subagent launch instruction when its mode requires one.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.subagent_delegator import SubagentDelegator


class StubDelegateInstructionBuilder:
    def build(self, prompt: str) -> str:
        return f"STUB[{prompt}]"


class TestSubagentDelegator(unittest.TestCase):

    def test_wraps_the_body_with_a_launch_instruction_for_subagent_mode(self):
        sut = SubagentDelegator(delegate_instruction_builder=StubDelegateInstructionBuilder())

        result = sut.wrap_if_subagent("Do the thing.", {"mode": "subagent"})

        self.assertEqual(result, "Launch a subagent with the following prompt:\n\nSTUB[Do the thing.]")

    def test_returns_the_body_unchanged_for_non_subagent_modes(self):
        sut = SubagentDelegator(delegate_instruction_builder=StubDelegateInstructionBuilder())

        result = sut.wrap_if_subagent("Do the thing.", {"mode": "inline"})

        self.assertEqual(result, "Do the thing.")

    def test_returns_the_body_unchanged_when_execution_has_no_mode(self):
        sut = SubagentDelegator(delegate_instruction_builder=StubDelegateInstructionBuilder())

        result = sut.wrap_if_subagent("Do the thing.", {})

        self.assertEqual(result, "Do the thing.")


if __name__ == "__main__":
    unittest.main()
