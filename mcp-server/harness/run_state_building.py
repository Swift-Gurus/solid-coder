"""Defines construction of reconstructed run state."""

from __future__ import annotations

from typing import Protocol

from harness.run_state import RunState


"""
solid-name: RunStateBuilding
solid-category: abstraction
solid-spec: [SPEC-030]
solid-description: Contract for creating mutable run state and finalizing it as an immutable model.
"""
class RunStateBuilding(Protocol):
    def empty(self) -> dict: ...
    def finish(self, state: dict) -> RunState: ...
