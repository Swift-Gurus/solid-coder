"""Records the project directory associated with an agent session."""

from pathlib import Path
from typing import Callable


"""
solid-name: SessionProjectDirectoryRecorder
solid-category: service
solid-description: Persists the canonical project directory associated with a session.
"""
class SessionProjectDirectoryRecorder:

    def __init__(self, context_path: Callable[[str], Path]) -> None:
        self._context_path = context_path

    def record(self, session_id: str, project_directory: Path) -> None:
        destination = self._context_path(session_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            str(project_directory.resolve()),
            encoding="utf-8",
        )
