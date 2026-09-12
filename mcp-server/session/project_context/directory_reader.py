"""Reads project directories associated with managed sessions."""

from pathlib import Path
from typing import Optional, Protocol

from session.project_context.path import SessionProjectContextPathResolving


"""
solid-name: SessionProjectDirectoryReading
solid-category: abstraction
solid-description: Contract for reading a session-scoped project directory.
"""
class SessionProjectDirectoryReading(Protocol):
    def read(self, session_id: str) -> Optional[Path]: ...


"""
solid-name: SessionProjectDirectoryReader
solid-category: service
solid-description: Retrieves the canonical project directory associated with a session.
"""
class SessionProjectDirectoryReader(SessionProjectDirectoryReading):

    def __init__(
        self,
        context_path_resolver: SessionProjectContextPathResolving,
    ) -> None:
        self._context_path_resolver = context_path_resolver

    def read(self, session_id: str) -> Optional[Path]:
        source = self._context_path_resolver.resolve(session_id)
        if not source.is_file():
            return None
        project_directory = source.read_text(encoding="utf-8").strip()
        return Path(project_directory) if project_directory else None
