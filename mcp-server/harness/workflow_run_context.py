"""Defines the typed values available while evaluating a workflow run."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.step_outputs import StepOutputs
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_alias_results import WorkflowAliasResults

if TYPE_CHECKING:
    from harness.step_skip import StepSkip


"""
solid-name: WorkflowRunContext
solid-category: model
solid-spec: [SPEC-030, SPEC-031, SPEC-037]
solid-description: Carries typed workflow parameters, completed outputs, retry details, and iteration state.
"""
@dataclass(frozen=True)
class WorkflowRunContext:
    parameters: WorkflowContextValues[object] = field(
        default_factory=WorkflowContextValues
    )
    completed_steps: WorkflowContextValues[StepOutputs] = field(
        default_factory=WorkflowContextValues
    )
    skipped_steps: WorkflowContextValues[StepSkip] = field(
        default_factory=WorkflowContextValues
    )
    rejection_reasons: WorkflowContextValues[str] = field(
        default_factory=WorkflowContextValues
    )
    attempts_used: WorkflowContextValues[int] = field(
        default_factory=WorkflowContextValues
    )
    workflows: WorkflowContextValues[WorkflowAliasResults] = field(
        default_factory=WorkflowContextValues
    )
    item: ResolvedWorkflowContextValue[object] = field(
        default_factory=lambda: ResolvedWorkflowContextValue(present=False)
    )
