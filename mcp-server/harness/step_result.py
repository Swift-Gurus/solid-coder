"""
solid-name: StepResult
solid-category: model
solid-spec: [SPEC-031]
solid-description: Captures a step execution's outcome and optional rejection information.
"""

from __future__ import annotations

from dataclasses import dataclass

from harness.authored_step_coordinate import AuthoredStepCoordinate
from harness.batch_step_presentation import BatchStepPresentation


@dataclass(frozen=True)
class StepResult:
    step_id: str
    instance_id: str
    prompt: str
    execution: dict
    rejection_reason: str | None = None
    batch: BatchStepPresentation | None = None
    submission_id: str | None = None
    authored_step: AuthoredStepCoordinate | None = None
