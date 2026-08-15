"""
solid-name: FlowStatusResult
solid-category: model
solid-spec: [SPEC-031, SPEC-037]
solid-description: Read-only snapshot of a flow execution's current state.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.step_skip_status import StepSkipStatus
from harness.workflow_condition_status import WorkflowConditionStatus


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
    skipped: list[StepSkipStatus] = field(default_factory=list)
    workflow_condition: WorkflowConditionStatus | None = None
    error: str | None = None
