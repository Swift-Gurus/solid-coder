"""
solid-description: Contract for evaluating a single expression against a run context to its raw Python value.
solid-category: abstraction
"""

from __future__ import annotations

from typing import Any, Protocol


class ExpressionEvaluating(Protocol):
    """
    solid-description: Contract for evaluating a single expression against a run context, returning the raw Python value without stringification.
    solid-category: abstraction
    """

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any: ...