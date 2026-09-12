"""Verifies durable session-to-project context used by plugin MCP servers."""

import sys
import tempfile
import unittest
from pathlib import Path


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER_DIRECTORY = _REPOSITORY_ROOT / "mcp-server"
if str(_MCP_SERVER_DIRECTORY) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER_DIRECTORY))

from session.project_context import (  # noqa: E402
    SessionProjectContextPathResolver,
    SessionProjectDirectoryReader,
    SessionProjectDirectoryRecording,
    SessionProjectDirectoryRecorder,
)


"""
solid-name: TestSessionProjectDirectoryContext
solid-category: unit-test
solid-description: Proves session-scoped project roots are persisted and recovered without relying on an MCP process working directory.
"""
class TestSessionProjectDirectoryContext(unittest.TestCase):

    def test_recording_contract_lives_with_its_first_implementation(self) -> None:
        self.assertEqual(
            SessionProjectDirectoryRecording.__module__,
            SessionProjectDirectoryRecorder.__module__,
        )

    def test_records_and_reads_the_project_directory_for_one_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context_path_resolver = SessionProjectContextPathResolver(
                Path(directory)
            )
            recorder = SessionProjectDirectoryRecorder(context_path_resolver)
            reader = SessionProjectDirectoryReader(context_path_resolver)
            project_directory = Path(directory) / "project"

            recorder.record("session-1", project_directory)

            self.assertEqual(reader.read("session-1"), project_directory.resolve())

    def test_returns_none_for_an_unknown_session(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            context_path_resolver = SessionProjectContextPathResolver(
                Path(directory)
            )
            reader = SessionProjectDirectoryReader(context_path_resolver)

            self.assertIsNone(reader.read("missing-session"))


if __name__ == "__main__":
    unittest.main()
