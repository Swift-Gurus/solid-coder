"""
solid-name: SessionIdReading
solid-category: abstraction
solid-spec: [SPEC-013]
solid-description: Contract for reading a session identifier from the current request context.
"""

from __future__ import annotations

from typing import Protocol


class SessionIdReading(Protocol):

    def read_session_id(self) -> str: ...
