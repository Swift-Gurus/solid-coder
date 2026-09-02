"""Resolves the durable project-context path for one session."""

from pathlib import Path


"""
solid-name: SessionProjectContextPathResolver
solid-category: service
solid-description: Validates session identities and resolves their project-context file paths.
"""
class SessionProjectContextPathResolver:

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
