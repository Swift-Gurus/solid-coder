"""
solid-name: TurnAdvancing
solid-category: abstraction
solid-spec: [SPEC-031]
solid-description: Contract that defines advancing the run's state upon turn completion.
"""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState


class TurnAdvancing(Protocol):

    def advance(self, events_path: str) -> RunState: ...
