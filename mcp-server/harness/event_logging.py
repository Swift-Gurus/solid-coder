"""
solid-description: Contract for appending events to an event log and replaying them to reconstruct state.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState


class EventLogging(Protocol):
    """
    solid-description: Contract for appending events to a log and replaying them to reconstruct state.
    solid-category: abstraction
    """

    def append(self, path: str, event_type: str, payload: dict) -> None: ...
    def replay(self, path: str) -> RunState: ...
