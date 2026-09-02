"""Defines durable completion state for one child workflow step."""

from __future__ import annotations

from dataclasses import dataclass

from harness.step_outputs import StepOutputs


"""
solid-name: IncludedWorkflowStepCompletion
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries explicit nested-workflow, local-step, execution, source, and output identity for one completed child step.
"""
@dataclass(frozen=True)
class IncludedWorkflowStepCompletion:
    workflow_instance_id: str
    parent_workflow_instance_id: str | None
    local_step_id: str
    execution_step_id: str
    instance_id: str
    workflow_source_index: int | None
    item: object
    outputs: StepOutputs
