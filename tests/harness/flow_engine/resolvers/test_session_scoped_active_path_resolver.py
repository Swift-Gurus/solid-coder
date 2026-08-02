"""
solid-name: test_session_scoped_active_path_resolver
solid-category: unit-test
solid-spec: [SPEC-013]
solid-description: Tests resolving the active-run pointer file path, scoped per session when available.
"""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.session_scoped_active_path_resolver import SessionScopedActivePathResolver


class StubSessionIdReader:
    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def read_session_id(self) -> str:
        return self._session_id


class TestSessionScopedActivePathResolver(unittest.TestCase):

    def test_resolves_to_active_json_when_no_reader_injected(self):
        sut = SessionScopedActivePathResolver()

        self.assertEqual(sut.resolve(Path("/runs")), Path("/runs/active.json"))

    def test_resolves_to_active_json_when_reader_returns_empty_string(self):
        sut = SessionScopedActivePathResolver(session_id_reader=StubSessionIdReader(""))

        self.assertEqual(sut.resolve(Path("/runs")), Path("/runs/active.json"))

    def test_resolves_to_session_scoped_filename_when_session_id_present(self):
        sut = SessionScopedActivePathResolver(session_id_reader=StubSessionIdReader("session-42"))

        self.assertEqual(sut.resolve(Path("/runs")), Path("/runs/active-session-42.json"))


if __name__ == "__main__":
    unittest.main()
