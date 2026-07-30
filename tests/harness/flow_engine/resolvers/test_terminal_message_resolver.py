"""
solid-name: test_terminal_message_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests resolving the message to show when a flow result has an error or a terminal status.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.terminal_message_resolver import TerminalMessageResolver


class TestTerminalMessageResolver(unittest.TestCase):

    def setUp(self):
        self.sut = TerminalMessageResolver()

    def test_returns_the_error_when_set_regardless_of_status(self):
        result = self.sut.resolve("boom", "done")

        self.assertEqual(result, "boom")

    def test_returns_flow_complete_for_done_status_with_no_error(self):
        result = self.sut.resolve(None, "done")

        self.assertEqual(result, "Flow complete.")

    def test_returns_none_for_a_non_terminal_status_with_no_error(self):
        result = self.sut.resolve(None, "ready")

        self.assertIsNone(result)

    def test_returns_none_when_both_error_and_status_are_none(self):
        result = self.sut.resolve(None, None)

        self.assertIsNone(result)


if __name__ == "__main__":
    unittest.main()
