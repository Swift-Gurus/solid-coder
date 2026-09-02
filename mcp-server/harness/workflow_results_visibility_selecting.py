"""Defines workflow-result visibility selection for one execution scope."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.workflow_alias_results import WorkflowAliasResults
from harness.workflow_context_values import WorkflowContextValues


"""
solid-name: WorkflowResultsVisibilitySelecting
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for exposing only included-workflow results owned by the current execution scope.
"""
class WorkflowResultsVisibilitySelecting(Protocol):
    def select(
        self,
        workflows: WorkflowContextValues[WorkflowAliasResults],
        workflow_instance: IncludedWorkflowInstance | None,
    ) -> WorkflowContextValues[WorkflowAliasResults]: ...
