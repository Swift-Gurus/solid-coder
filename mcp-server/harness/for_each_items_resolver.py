"""Resolves workflow iteration expressions into ordered item collections."""

from __future__ import annotations

import re
from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.models import FlowValidationError

_SINGLE_EXPRESSION = re.compile(r"^\{\{([^}]+)\}\}$")


"""
solid-name: ForEachItemsResolver
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Resolves and validates workflow for-each expressions as ordered item collections.
"""
class ForEachItemsResolver(ForEachItemsResolving):
    def __init__(self, evaluator: ExpressionEvaluating) -> None:
        self._evaluator = evaluator

    def resolve(
        self,
        step_id: str,
        expression: str,
        context: dict[str, Any],
    ) -> list[Any]:
        expression_match = _SINGLE_EXPRESSION.match(expression.strip())
        normalized_expression = (
            expression_match.group(1).strip()
            if expression_match
            else expression.strip()
        )
        value = self._evaluator.evaluate(normalized_expression, context)
        if not isinstance(value, list):
            raise FlowValidationError(
                f"Step '{step_id}' for_each must resolve to an array"
            )
        return value
