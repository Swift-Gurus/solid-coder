"""Defines the nested execution scope of one included workflow instance."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Optional

from harness.combined_rule_presentation import CombinedRulePresentation
from harness.condition_declaration import ConditionDeclaration
from harness.for_each_declaration import ForEachDeclaration
from harness.included_rule_workflow import IncludedRuleWorkflow
from harness.included_workflow_step_identities import IncludedWorkflowStepIdentities
from harness.workflow_context_values import WorkflowContextValues


"""
solid-name: IncludedWorkflowInstance
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents the execution scope of one materialized included workflow.
"""
@dataclass(frozen=True)
class IncludedWorkflowInstance:
    alias: str
    instance_id: str
    source_index: int
    source_item: object
    owner_instance_id: str | None = None
    condition: ConditionDeclaration | None = None
    inputs: WorkflowContextValues[object] = field(
        default_factory=WorkflowContextValues
    )
    steps: IncludedWorkflowStepIdentities = field(
        default_factory=IncludedWorkflowStepIdentities
    )
    rule_workflow: IncludedRuleWorkflow | None = None
    for_each: Optional[ForEachDeclaration] = None
    combined_presentation: CombinedRulePresentation | None = None
