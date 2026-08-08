"""Defines reconstructed workflow run state."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.step_outputs import StepOutputs


"""
solid-name: RunState
solid-category: model
solid-spec: [SPEC-030, SPEC-027]
solid-description: Represents completed work, active steps, attempts, rejection reasons, and terminal state for a run.
"""
@dataclass(frozen=True)
class RunState:
    completed: dict[str, StepOutputs]
    running: list[str]
    turn_count: int
    status: str
    attempts_used: dict[str, int] = field(default_factory=dict)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
