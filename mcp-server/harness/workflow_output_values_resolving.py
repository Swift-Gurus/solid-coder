"""Defines resolution of published workflow-output values."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_values import WorkflowOutputValues
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowOutputValuesResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving and validating the declared outputs of one workflow instance.
"""
class WorkflowOutputValuesResolving(Protocol):
    def resolve(
        self,
        instance: IncludedWorkflowInstance,
        outputs: list[WorkflowOutputDeclaration],
        context: WorkflowRunContext,
    ) -> WorkflowOutputValues: ...
