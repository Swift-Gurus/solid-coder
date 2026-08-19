"""Resolves operation bindings through the shared workflow expression engine."""

from harness.operation_inputs_resolving import OperationInputsResolving
from harness.operation_step import OperationStep
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_input_bindings_resolving import WorkflowInputBindingsResolving
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: OperationInputsResolver
solid-category: service
solid-spec: [SPEC-010, SPEC-040]
solid-description: Resolves typed operation input values from workflow runtime context.
"""
class OperationInputsResolver(OperationInputsResolving):
    def __init__(
        self,
        bindings_resolver: WorkflowInputBindingsResolving,
    ) -> None:
        self._bindings_resolver = bindings_resolver

    def resolve(
        self,
        operation: OperationStep,
        context: WorkflowRunContext,
    ) -> WorkflowContextValues[object]:
        return self._bindings_resolver.resolve(
            operation.input_bindings,
            context,
        )
