"""Defines runtime resolution of typed operation inputs."""

from typing import Protocol

from harness.operation_step import OperationStep
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: OperationInputsResolving
solid-category: abstraction
solid-spec: [SPEC-010, SPEC-040]
solid-description: Contract for resolving operation bindings against one step runtime context.
"""
class OperationInputsResolving(Protocol):
    def resolve(
        self,
        operation: OperationStep,
        context: WorkflowRunContext,
    ) -> WorkflowContextValues[object]: ...
