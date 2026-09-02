"""Resolves the project directory for the current MCP request."""

import os
from pathlib import Path
from typing import Callable, Mapping, Optional

from harness.session_id_reading import SessionIdReading


"""
solid-name: McpRequestContextProjectDirectoryReader
solid-category: service
solid-description: Resolves the current MCP request project from host and session context.
"""
class McpRequestContextProjectDirectoryReader:

    def __init__(
        self,
        session_reader: SessionIdReading,
        session_project_directory: Callable[[str], Optional[Path]],
        env: Mapping[str, str] = os.environ,
        cwd_factory: Callable[[], Path] = Path.cwd,
    ) -> None:
        self._session_reader = session_reader
        self._session_project_directory = session_project_directory
        self._env = env
        self._cwd_factory = cwd_factory

    def read(self) -> Path:
        claude_project_directory = self._env.get("CLAUDE_PROJECT_DIR", "")
        if claude_project_directory:
            return Path(claude_project_directory)

        session_id = self._session_reader.read_session_id()
        if session_id:
            recorded_project_directory = self._session_project_directory(session_id)
            if recorded_project_directory is not None:
                return recorded_project_directory

        return self._cwd_factory()
