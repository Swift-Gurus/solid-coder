"""
solid-name: ExecutionOutcome
solid-category: model
solid-spec: [SPEC-031]
solid-description: Represents the outcome of executing a flow's ready steps.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.flow_next_result import FlowNextResult
from harness.step_result import StepResult


@dataclass(frozen=True)
class ExecutionOutcome:
    steps: list[StepResult] = field(default_factory=list)
    terminal: FlowNextResult | None = None
    error: str | None = None
