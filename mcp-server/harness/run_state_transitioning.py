"""Defines one event-driven run-state transition."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: RunStateTransitioning
solid-category: abstraction
solid-spec: [SPEC-030]
solid-description: Contract for applying one workflow event to mutable reconstructed run state.
"""
class RunStateTransitioning(Protocol):
    def apply(self, state: dict, event: dict) -> None: ...
