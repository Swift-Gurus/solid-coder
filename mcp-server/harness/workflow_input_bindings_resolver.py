"""Resolves declared child-workflow input expressions."""

from harness.expression_evaluating import ExpressionEvaluating
from harness.expression_normalizing import ExpressionNormalizing
from harness.resolved_workflow_input import ResolvedWorkflowInput
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
        expression_normalizer: ExpressionNormalizing,
    ) -> None:
        self._evaluator = evaluator
        self._expression_normalizer = expression_normalizer

    def resolve(
        self,
        bindings: list[WorkflowInputBinding],
        context: WorkflowRunContext,
    ) -> list[ResolvedWorkflowInput]:
        return [
            ResolvedWorkflowInput(
                name=binding.name,
                value=self._evaluator.evaluate(
                    self._expression_normalizer.normalize(binding.expression),
                    context,
                ),
            )
            for binding in bindings
        ]
