"""Defines resolution of child-workflow input bindings."""

from typing import Protocol

from harness.resolved_workflow_input import ResolvedWorkflowInput
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowInputBindingsResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving declared child workflow inputs from a parent runtime context.
"""
class WorkflowInputBindingsResolving(Protocol):
    def resolve(
        self,
        bindings: list[WorkflowInputBinding],
        context: WorkflowRunContext,
    ) -> list[ResolvedWorkflowInput]: ...
