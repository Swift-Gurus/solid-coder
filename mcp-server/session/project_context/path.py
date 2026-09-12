"""Resolves durable project-context paths for managed sessions."""

from pathlib import Path
from typing import Protocol


"""
solid-name: SessionProjectContextPathResolving
solid-category: abstraction
solid-description: Contract for session-scoped project-context path resolution.
"""
class SessionProjectContextPathResolving(Protocol):
    def resolve(self, session_id: str) -> Path: ...


"""
solid-name: SessionProjectContextPathResolver
solid-category: service
solid-description: Validates session identities and resolves their project-context file paths.
"""
class SessionProjectContextPathResolver(SessionProjectContextPathResolving):

    def __init__(
        self,
        root_directory: Path = Path.home() / ".solid-coder" / "sessions",
    ) -> None:
        self._root_directory = root_directory

    def resolve(self, session_id: str) -> Path:
        if (
            not session_id
            or session_id in {".", ".."}
            or Path(session_id).name != session_id
        ):
            raise ValueError("Session ID must be a non-empty path component")
        return self._root_directory / session_id / "project-root"
