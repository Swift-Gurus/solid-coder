"""
solid-description: Contract for reconstructing execution state from a sequence of parsed events.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Protocol

from harness.models import RunState


class RunStateReconstructing(Protocol):
    """
    solid-description: Contract for reconstructing execution state from a sequence of parsed events.
    solid-category: abstraction
    """

    def reconstruct(self, events: list[dict]) -> RunState: ...
