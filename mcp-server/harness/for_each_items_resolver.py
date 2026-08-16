"""Resolves workflow iteration expressions into ordered item collections."""

from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.expression_normalizing import ExpressionNormalizing
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.models import FlowValidationError
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: ForEachItemsResolver
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Resolves and validates workflow for-each expressions as ordered item collections.
"""
class ForEachItemsResolver(ForEachItemsResolving):
    def __init__(
        self,
        evaluator: ExpressionEvaluating,
        expression_normalizer: ExpressionNormalizing,
    ) -> None:
        self._evaluator = evaluator
        self._expression_normalizer = expression_normalizer

    def resolve(
        self,
        step_id: str,
        expression: str,
        context: WorkflowRunContext,
    ) -> list[Any]:
        normalized_expression = self._expression_normalizer.normalize(expression)
        value = self._evaluator.evaluate(normalized_expression, context)
        if not isinstance(value, list):
            raise FlowValidationError(
                f"Step '{step_id}' for_each must resolve to an array"
            )
        return value
