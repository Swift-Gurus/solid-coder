"""Defines reconstructed workflow run state."""

from __future__ import annotations

from dataclasses import dataclass, field

from harness.step_instance_completion import StepInstanceCompletion
from harness.step_outputs import StepOutputs
from harness.step_skip import StepSkip
from harness.workflow_condition_decision import WorkflowConditionDecision


"""
solid-name: RunState
solid-category: model
solid-spec: [SPEC-030, SPEC-027, SPEC-037]
solid-description: Represents completed, skipped, active, attempted, and terminal workflow-run state.
"""
@dataclass(frozen=True)
class RunState:
    completed: dict[str, StepOutputs]
    running: list[str]
    turn_count: int
    status: str
    workflow_condition_decision: WorkflowConditionDecision | None = None
    completed_instances: dict[str, StepInstanceCompletion] = field(default_factory=dict)
    skipped: dict[str, StepSkip] = field(default_factory=dict)
    skipped_instances: dict[str, StepSkip] = field(default_factory=dict)
    attempts_used: dict[str, int] = field(default_factory=dict)
    attempt_step_ids: dict[str, str] = field(default_factory=dict)
    rejection_reasons: dict[str, str] = field(default_factory=dict)
