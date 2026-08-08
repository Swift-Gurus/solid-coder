"""
solid-name: test_static_session_id_reader
solid-category: unit-test
solid-spec: [SPEC-031]
solid-description: Tests returning a fixed session identifier known at construction time.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.static_session_id_reader import StaticSessionIdReader


class TestStaticSessionIdReader(unittest.TestCase):

    def test_returns_the_configured_session_id(self):
        sut = StaticSessionIdReader("session-abc")

        self.assertEqual(sut.read_session_id(), "session-abc")

    def test_defaults_to_empty_string_when_constructed_with_no_argument(self):
        sut = StaticSessionIdReader()

        self.assertEqual(sut.read_session_id(), "")


if __name__ == "__main__":
    unittest.main()
