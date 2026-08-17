"""Defines the nested execution scope of one included workflow instance."""

from dataclasses import dataclass, field

from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.workflow_context_values import WorkflowContextValues


"""
solid-name: IncludedWorkflowInstance
solid-category: model
solid-spec: [SPEC-037]
solid-description: Carries one included workflow's identity, source association, resolved inputs, and child step identities.
"""
@dataclass(frozen=True)
class IncludedWorkflowInstance:
    alias: str
    instance_id: str
    source_index: int
    source_item: object
    inputs: WorkflowContextValues[object] = field(
        default_factory=WorkflowContextValues
    )
    steps: IncludedWorkflowStepIdentities = field(
        default_factory=IncludedWorkflowStepIdentities
    )
