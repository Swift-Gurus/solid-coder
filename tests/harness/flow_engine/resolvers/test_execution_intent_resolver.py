"""
solid-name: test_execution_intent_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests execution intent to execution mode resolution based on runtime environment.
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.execution_intent_resolver import ExecutionIntentResolver


class TestExecutionIntentResolver(unittest.TestCase):

    def setUp(self):
        self.resolver = ExecutionIntentResolver()

    def test_inline_intent_always_returns_inline_mode_in_claude_code(self):
        result = self.resolver.resolve("inline", "claude-code")

        self.assertEqual(result, {"mode": "inline"})

    def test_inline_intent_always_returns_inline_mode_outside_claude_code(self):
        result = self.resolver.resolve("inline", "")

        self.assertEqual(result, {"mode": "inline"})

    def test_parallel_isolated_returns_subagent_in_claude_code(self):
        result = self.resolver.resolve("parallel_isolated", "claude-code")

        self.assertEqual(result, {"mode": "subagent"})

    def test_parallel_isolated_returns_session_outside_claude_code(self):
        result = self.resolver.resolve("parallel_isolated", "")

        self.assertEqual(result, {"mode": "session"})

    def test_sequential_isolated_returns_subagent_in_claude_code(self):
        result = self.resolver.resolve("sequential_isolated", "claude-code")

        self.assertEqual(result, {"mode": "subagent"})

    def test_sequential_isolated_returns_session_outside_claude_code(self):
        result = self.resolver.resolve("sequential_isolated", "")

        self.assertEqual(result, {"mode": "session"})


if __name__ == "__main__":
    unittest.main()
