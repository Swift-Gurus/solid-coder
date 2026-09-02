"""Selects included-workflow results visible to one execution scope."""

from __future__ import annotations

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.workflow_alias_results import WorkflowAliasResults
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_results_visibility_selecting import (
    WorkflowResultsVisibilitySelecting,
)


"""
solid-name: WorkflowResultsVisibilitySelector
solid-category: service
solid-spec: [SPEC-037]
solid-description: Exposes included-workflow results visible to one execution scope.
"""
class WorkflowResultsVisibilitySelector(WorkflowResultsVisibilitySelecting):
    def select(
        self,
        workflows: WorkflowContextValues[WorkflowAliasResults],
        workflow_instance: IncludedWorkflowInstance | None,
    ) -> WorkflowContextValues[WorkflowAliasResults]:
        if workflow_instance is None:
            visible = [
                entry
                for entry in workflows.entries
                if entry.value.owner_alias is None
                and entry.value.runtime_owner_instance_id is None
            ]
        else:
            visible = [
                entry
                for entry in workflows.entries
                if entry.value.runtime_owner_instance_id
                == workflow_instance.instance_id
                or (
                    entry.value.runtime_owner_instance_id is None
                    and entry.value.owner_alias == workflow_instance.alias
                )
            ]
        return WorkflowContextValues(entries=[
            WorkflowContextValue(
                name=entry.value.authored_alias,
                value=entry.value,
            )
            for entry in visible
        ])
