"""Builds the mutable and immutable forms of reconstructed run state."""

from __future__ import annotations

from harness.run_state import RunState


"""
solid-name: RunStateBuilder
solid-category: service
solid-spec: [SPEC-030]
solid-description: Creates empty reconstruction state and finalizes it as an immutable run-state model.
"""
class RunStateBuilder:
    def empty(self) -> dict:
        return {
            "completed": {},
            "running": [],
            "turn_count": 0,
            "status": "in_progress",
            "attempts_used": {},
            "rejection_reasons": {},
        }

    def finish(self, state: dict) -> RunState:
        return RunState(**state)
