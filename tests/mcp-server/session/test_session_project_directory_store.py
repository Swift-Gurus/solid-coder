"""Verifies durable session-to-project context used by plugin MCP servers."""

import sys
import tempfile
import unittest
from pathlib import Path


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_SESSION_DIRECTORY = _REPOSITORY_ROOT / "mcp-server" / "session"
if str(_SESSION_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_SESSION_DIRECTORY))

from session_project_context_path_resolver import (  # noqa: E402
    SessionProjectContextPathResolver,
)
from session_project_directory_reader import SessionProjectDirectoryReader  # noqa: E402
from session_project_directory_recorder import (  # noqa: E402
    SessionProjectDirectoryRecorder,
)


"""
solid-name: TestSessionProjectDirectoryContext
solid-category: unit-test
solid-description: Proves session-scoped project roots are persisted and recovered without relying on an MCP process working directory.
"""
class TestSessionProjectDirectoryContext(unittest.TestCase):

    def test_records_and_reads_the_project_directory_for_one_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context_path = SessionProjectContextPathResolver(
                Path(directory)
            ).resolve
            recorder = SessionProjectDirectoryRecorder(context_path)
            reader = SessionProjectDirectoryReader(context_path)
            project_directory = Path(directory) / "project"

            recorder.record("session-1", project_directory)

            self.assertEqual(reader.read("session-1"), project_directory.resolve())

    def test_returns_none_for_an_unknown_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context_path = SessionProjectContextPathResolver(
                Path(directory)
            ).resolve
            reader = SessionProjectDirectoryReader(context_path)

            self.assertIsNone(reader.read("missing-session"))


if __name__ == "__main__":
    unittest.main()
