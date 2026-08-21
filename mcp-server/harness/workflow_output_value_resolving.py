"""Defines resolution of one published workflow-output value."""

from __future__ import annotations

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.workflow_output_declaration import WorkflowOutputDeclaration
from harness.workflow_output_value import WorkflowOutputValue
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowOutputValueResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving and validating one declared workflow output.
"""
class WorkflowOutputValueResolving(Protocol):
    def resolve(
        self,
        instance: IncludedWorkflowInstance,
        output: WorkflowOutputDeclaration,
        context: WorkflowRunContext,
    ) -> WorkflowOutputValue: ...
