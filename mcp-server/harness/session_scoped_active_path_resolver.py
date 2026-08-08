"""
solid-name: SessionScopedActivePathResolver
solid-category: service
solid-spec: [SPEC-031]
solid-description: Resolves the path to the active file, scoped by session.
"""

from __future__ import annotations

from pathlib import Path

from harness.session_id_reading import SessionIdReading
from harness.session_scoped_active_path_resolving import SessionScopedActivePathResolving


class SessionScopedActivePathResolver(SessionScopedActivePathResolving):

    def __init__(self, session_id_reader: SessionIdReading | None = None) -> None:
        self._session_id_reader = session_id_reader

    def resolve(self, base_dir: Path) -> Path:
        session_id = self._session_id_reader.read_session_id() if self._session_id_reader else ""
        filename = f"active-{session_id}.json" if session_id else "active.json"
        return base_dir / filename
