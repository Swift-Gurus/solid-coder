"""Defines runtime context resolution for one workflow step."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowStepContextResolving
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for resolving the parameters, completed outputs, and item visible to one executable workflow step.
"""
class WorkflowStepContextResolving(Protocol):
    def resolve(
        self,
        context: WorkflowRunContext,
        workflow_instance: IncludedWorkflowInstance | None,
        item: object,
    ) -> WorkflowRunContext: ...
