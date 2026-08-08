"""
solid-name: StepResult
solid-category: model
solid-spec: [SPEC-031]
solid-description: Captures a step execution's outcome and optional rejection information.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StepResult:
    step_id: str
    instance_id: str
    prompt: str
    execution: dict
    rejection_reason: str | None = None
