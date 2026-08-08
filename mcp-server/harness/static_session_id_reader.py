"""
solid-name: StaticSessionIdReader
solid-category: service
solid-spec: [SPEC-031]
solid-description: Provides consistent session identification.
"""

from __future__ import annotations


class StaticSessionIdReader:

    def __init__(self, session_id: str = "") -> None:
        self._session_id = session_id

    def read_session_id(self) -> str:
        return self._session_id
