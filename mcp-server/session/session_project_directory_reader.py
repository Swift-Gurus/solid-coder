"""Reads the project directory associated with an agent session."""

from pathlib import Path
from typing import Callable, Optional


"""
solid-name: SessionProjectDirectoryReader
solid-category: service
solid-description: Retrieves the canonical project directory associated with a session.
"""
class SessionProjectDirectoryReader:

    def __init__(self, context_path: Callable[[str], Path]) -> None:
        self._context_path = context_path

    def read(self, session_id: str) -> Optional[Path]:
        source = self._context_path(session_id)
        if not source.is_file():
            return None
        project_directory = source.read_text(encoding="utf-8").strip()
        return Path(project_directory) if project_directory else None
