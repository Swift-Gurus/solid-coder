from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.interpolation_error_creating import InterpolationErrorCreating
from harness.nested_value_resolving import NestedValueResolving


"""
solid-name: ExpressionResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-034, SPEC-037]
solid-description: Resolves an unfiltered workflow expression from runtime context.
"""
class ExpressionResolver(ExpressionEvaluating):
    def __init__(
        self,
        step_output_resolver: ExpressionEvaluating,
        nested_value_resolver: NestedValueResolving,
        error_factory: InterpolationErrorCreating,
    ) -> None:
        self._step_outputs = step_output_resolver
        self._nested_values = nested_value_resolver
        self._error_factory = error_factory

    def evaluate(self, expr: str, context: dict[str, Any]) -> Any:
        parts = expr.split(".")
        if parts[0] == "steps":
            return self._step_outputs.evaluate(expr, context)
        if parts[0] == "params":
            return self._resolve_parameter(parts, expr, context)
        root_name = parts[0]
        if root_name not in context:
            raise self._error_factory.create(expr)
        return self._nested_values.resolve(context[root_name], parts[1:], expr)

    def _resolve_parameter(
        self,
        parts: list[str],
        reference: str,
        context: dict[str, Any],
    ) -> object:
        if len(parts) < 2:
            raise self._error_factory.create(reference)
        params = context.get("params", {})
        parameter_name = parts[1]
        if parameter_name not in params:
            raise self._error_factory.create(
                reference,
                f"parameter '{parameter_name}' not found in context",
            )
        return self._nested_values.resolve(
            params[parameter_name],
            parts[2:],
            reference,
        )
