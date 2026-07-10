"""
solid-name: FlowStartResult
solid-category: model
solid-spec: [SPEC-013]
solid-description: Container for the execution identifier and initial steps of a flow.
"""

from __future__ import annotations

from dataclasses import dataclass

from harness.step_result import StepResult


@dataclass(frozen=True)
class FlowStartResult:
    run_id: str
    steps: list[StepResult]
