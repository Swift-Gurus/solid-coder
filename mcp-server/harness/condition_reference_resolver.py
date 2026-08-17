"""Resolves condition references through the shared expression engine."""

from __future__ import annotations

from harness.condition_reference_resolving import ConditionReferenceResolving
from harness.expression_evaluating import ExpressionEvaluating
from harness.interpolation_error import InterpolationError
from harness.resolved_condition_value import ResolvedConditionValue
from harness.workflow_expression import WorkflowExpression
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ConditionReferenceResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves workflow condition values while preserving absent-versus-null semantics.
"""
class ConditionReferenceResolver(ConditionReferenceResolving):
    def __init__(
        self,
        expression_evaluator: ExpressionEvaluating,
    ) -> None:
        self._expression_evaluator = expression_evaluator

    def resolve(
        self,
        reference: WorkflowExpression,
        context: WorkflowRunContext,
    ) -> ResolvedConditionValue:
        try:
            value = self._expression_evaluator.evaluate(reference.value, context)
            return ResolvedConditionValue(present=True, value=value)
        except InterpolationError:
            return ResolvedConditionValue(present=False)
