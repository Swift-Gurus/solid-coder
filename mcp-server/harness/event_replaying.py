"""
solid-name: EventReplaying
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract for restoring run state from a given path.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState


class EventReplaying(Protocol):

    def replay(self, path: str) -> RunState: ...
