"""
solid-name: ExpressionResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-034]
solid-description: Evaluates template expressions containing run parameters, step outputs, item values, and optional filters against a runtime flow context.
"""

from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.filter_resolver import FilterResolving
from harness.interpolation_error import InterpolationError
from harness.models import StepOutputs


class ExpressionResolver(ExpressionEvaluating):
    """
    solid-description: Evaluates a template expression containing variable references and optional filters against a runtime context.
    solid-category: service
    """

    def __init__(self, filter_resolver: FilterResolving) -> None:
        self._filters = filter_resolver

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any:
        if " | " in expr:
            raw_expr, filter_name = expr.split(" | ", 1)
            return self._filters.apply(self._lookup(raw_expr.strip(), context), filter_name.strip())
        return self._lookup(expr, context)

    def _lookup(self, expr: str, context: dict[str, Any]) -> Any:
        parts = expr.split(".")
        if parts[0] == "steps":
            return self._lookup_step(parts, context)
        if parts[0] == "params":
            return self._lookup_param(parts, context)
        if expr in context:
            return context[expr]
        raise InterpolationError(f"Unresolvable reference: '{expr}'")

    def _lookup_param(self, parts: list[str], context: dict[str, Any]) -> Any:
        if len(parts) != 2:
            joined = ".".join(parts)
            raise InterpolationError(
                f"Invalid params reference: expected 'params.<key>', got '{joined}'"
            )
        params = context.get("params", {})
        key = parts[1]
        if key not in params:
            raise InterpolationError(f"Unresolvable reference: parameter '{key}' not found in context")
        return params[key]

    def _lookup_step(self, parts: list[str], context: dict[str, Any]) -> Any:
        if len(parts) < 4 or parts[2] != "outputs":
            joined = ".".join(parts)
            raise InterpolationError(
                f"Invalid steps reference: expected 'steps.<id>.outputs.<name>', got '{joined}'"
            )
        step_id, output_name = parts[1], parts[3]
        steps: dict[str, StepOutputs] = context.get("steps", {})
        if step_id not in steps:
            raise InterpolationError(f"Unresolvable reference: step '{step_id}' not found in context")
        value = steps[step_id].get(output_name)
        if value is None:
            raise InterpolationError(
                f"Unresolvable reference: output '{output_name}' not found on step '{step_id}'"
            )
        return value
