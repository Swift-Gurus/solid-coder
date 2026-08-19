"""Resolves declared child-workflow input expressions."""

from harness.expression_evaluating import ExpressionEvaluating
from harness.workflow_context_value import WorkflowContextValue
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_input_binding import WorkflowInputBinding
from harness.workflow_input_bindings_resolving import WorkflowInputBindingsResolving
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: WorkflowInputBindingsResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves child workflow input expressions to their raw runtime values.
"""
class WorkflowInputBindingsResolver(WorkflowInputBindingsResolving):

    def __init__(
        self,
        evaluator: ExpressionEvaluating,
    ) -> None:
        self._evaluator = evaluator

    def resolve(
        self,
        bindings: list[WorkflowInputBinding],
        context: WorkflowRunContext,
    ) -> WorkflowContextValues[object]:
        return WorkflowContextValues(
            entries=[
                WorkflowContextValue(
                    name=binding.name,
                    value=self._evaluator.evaluate(
                        binding.expression.value,
                        context,
                    ),
                )
                for binding in bindings
            ]
        )
