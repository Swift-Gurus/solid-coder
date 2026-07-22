"""
solid-name: FlowStatusResult
solid-category: model
solid-spec: [SPEC-013]
solid-description: Read-only snapshot of a flow execution's current state.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class FlowStatusResult:
    flow: str
    run_id: str
    status: str
    turn_count: int
    max_turns: int
    completed: list[str]
    running: list[str]
    pending: list[str]
    error: str | None = None
