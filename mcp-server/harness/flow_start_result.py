"""
solid-name: FlowStartResult
solid-category: model
solid-spec: [SPEC-013]
solid-description: Represents the result of starting a flow execution, providing execution reference and step information.
"""

from __future__ import annotations

from dataclasses import dataclass

from harness.step_result import StepResult


@dataclass(frozen=True)
class FlowStartResult:
    run_id: str
    steps: list[StepResult]
    error: str | None = None