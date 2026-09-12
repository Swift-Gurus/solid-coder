"""Records project directories associated with managed sessions."""

from pathlib import Path
from typing import Protocol

from session.project_context.path import SessionProjectContextPathResolving


"""
solid-name: SessionProjectDirectoryRecording
solid-category: abstraction
solid-description: Contract for recording a session-scoped project directory.
"""
class SessionProjectDirectoryRecording(Protocol):
    def record(self, session_id: str, project_directory: Path) -> None: ...


"""
solid-name: SessionProjectDirectoryRecorder
solid-category: service
solid-description: Persists the canonical project directory associated with a session.
"""
class SessionProjectDirectoryRecorder(SessionProjectDirectoryRecording):

    def __init__(
        self,
        context_path_resolver: SessionProjectContextPathResolving,
    ) -> None:
        self._context_path_resolver = context_path_resolver

    def record(self, session_id: str, project_directory: Path) -> None:
        destination = self._context_path_resolver.resolve(session_id)
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_text(
            str(project_directory.resolve()),
            encoding="utf-8",
        )
