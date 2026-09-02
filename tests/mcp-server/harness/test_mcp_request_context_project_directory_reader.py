"""Verifies project-root resolution for plugin-hosted MCP calls."""

import sys
import unittest
from pathlib import Path
from typing import Optional


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER_DIRECTORY = _REPOSITORY_ROOT / "mcp-server"
for _directory in (
    _MCP_SERVER_DIRECTORY,
    _MCP_SERVER_DIRECTORY / "harness",
    _MCP_SERVER_DIRECTORY / "session",
):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from harness.mcp_request_context_project_directory_reader import (  # noqa: E402
    McpRequestContextProjectDirectoryReader,
)


class StubSessionReader:

    def __init__(self, session_id: str) -> None:
        self._session_id = session_id

    def read_session_id(self) -> str:
        return self._session_id


class StubProjectDirectoryReader:

    def __init__(self, project_directory: Optional[Path]) -> None:
        self._project_directory = project_directory

    def read(self, session_id: str) -> Optional[Path]:
        return self._project_directory


"""
solid-name: TestMcpRequestContextProjectDirectoryReader
solid-category: unit-test
solid-description: Proves MCP project resolution uses host context, session context, and process fallback in precedence order.
"""
class TestMcpRequestContextProjectDirectoryReader(unittest.TestCase):

    def test_prefers_claude_project_directory(self) -> None:
        reader = self._reader(
            env={"CLAUDE_PROJECT_DIR": "/claude/project"},
            session_project=Path("/session/project"),
        )

        self.assertEqual(reader.read(), Path("/claude/project"))

    def test_uses_session_project_recorded_by_the_start_hook(self) -> None:
        reader = self._reader(env={}, session_project=Path("/session/project"))

        self.assertEqual(reader.read(), Path("/session/project"))

    def test_falls_back_to_process_directory_without_host_context(self) -> None:
        reader = self._reader(env={}, session_project=None)

        self.assertEqual(reader.read(), Path("/plugin/cache"))

    @staticmethod
    def _reader(
        env: dict[str, str],
        session_project: Optional[Path],
    ) -> McpRequestContextProjectDirectoryReader:
        return McpRequestContextProjectDirectoryReader(
            session_reader=StubSessionReader("session-1"),
            session_project_directory=StubProjectDirectoryReader(
                session_project
            ).read,
            env=env,
            cwd_factory=lambda: Path("/plugin/cache"),
        )


if __name__ == "__main__":
    unittest.main()
