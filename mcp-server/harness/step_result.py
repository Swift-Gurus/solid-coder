"""
solid-name: StepResult
solid-category: model
solid-spec: [SPEC-013]
solid-description: Represents the execution outcome and retry state of a step.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepResult:
    step_id: str
    instance_id: str
    prompt: str
    execution: dict
    attempts_remaining: int | None = None
    rejection_reason: str | None = None
