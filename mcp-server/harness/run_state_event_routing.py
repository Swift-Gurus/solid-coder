"""Defines routing of workflow events to state transitions."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: RunStateEventRouting
solid-category: abstraction
solid-spec: [SPEC-030]
solid-description: Contract for routing a workflow event to its run-state transition.
"""
class RunStateEventRouting(Protocol):
    def route(self, state: dict, event: dict) -> None: ...
