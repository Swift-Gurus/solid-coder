"""
solid-description: Enables rendering template strings with embedded expression evaluation.
solid-category: service
"""

from __future__ import annotations

import re
from typing import Any, Protocol

from harness.expression_evaluating import ExpressionEvaluating


class TemplateRendering(Protocol):
    """
    solid-description: Contract for rendering template strings with provided context.
    solid-category: abstraction
    """

    def render(self, template: str, context: dict[str, Any]) -> str: ...


_EXPR_RE = re.compile(r"\{\{([^}]+)\}\}")


class Interpolator:
    """
    solid-description: Renders template strings by evaluating embedded expressions in a provided context.
    solid-category: service
    """

    def __init__(self, evaluator: ExpressionEvaluating) -> None:
        self._evaluator = evaluator

    def render(self, template: str, context: dict[str, Any]) -> str:
        def replace(match: re.Match) -> str:
            return str(self._evaluator.evaluate(match.group(1).strip(), context))

        return _EXPR_RE.sub(replace, template)

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any:
        return self._evaluator.evaluate(expr, context)