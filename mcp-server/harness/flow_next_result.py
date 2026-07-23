"""
solid-name: FlowNextResult
solid-category: model
solid-spec: [SPEC-013]
solid-description: Represents the result of a flow operation, conveying execution status, step results, and errors.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.step_result import StepResult


@dataclass(frozen=True)
class FlowNextResult:
    status: str
    steps: list[StepResult] = field(default_factory=list)
    error: str | None = None
