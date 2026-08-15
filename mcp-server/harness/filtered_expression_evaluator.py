"""Applies optional filters to resolved workflow expressions."""

from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.filter_resolver import FilterResolving


"""
solid-name: FilteredExpressionEvaluator
solid-category: service
solid-spec: [SPEC-030]
solid-description: Evaluates a workflow expression and applies its optional named filter.
"""
class FilteredExpressionEvaluator(ExpressionEvaluating):
    def __init__(
        self,
        expression_evaluator: ExpressionEvaluating,
        filter_resolver: FilterResolving,
    ) -> None:
        self._expression_evaluator = expression_evaluator
        self._filter_resolver = filter_resolver

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any:
        if " | " not in expr:
            return self._expression_evaluator.evaluate(expr, context)
        raw_expression, filter_name = expr.split(" | ", 1)
        value = self._expression_evaluator.evaluate(raw_expression.strip(), context)
        return self._filter_resolver.apply(value, filter_name.strip())
