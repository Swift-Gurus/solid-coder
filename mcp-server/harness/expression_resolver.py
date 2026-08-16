from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.interpolation_error_creating import InterpolationErrorCreating
from harness.nested_value_resolving import NestedValueResolving
from harness.workflow_context_values import WorkflowContextValues
from harness.workflow_run_context import WorkflowRunContext


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

    def evaluate(self, expr: str, context: WorkflowRunContext) -> Any:
        parts = expr.split(".")
        if parts[0] == "steps":
            return self._step_outputs.evaluate(expr, context)
        if parts[0] == "params":
            return self._resolve_parameter(parts, expr, context.parameters)
        if parts[0] == "rejection_reasons":
            return self._resolve_named_value(
                parts,
                expr,
                context.rejection_reasons,
            )
        if parts[0] == "attempts_used":
            return self._resolve_named_value(
                parts,
                expr,
                context.attempts_used,
            )
        if parts[0] == "item" and context.item.present:
            return self._nested_values.resolve(
                context.item.value,
                parts[1:],
                expr,
            )
        raise self._error_factory.create(expr)

    def _resolve_parameter(
        self,
        parts: list[str],
        reference: str,
        parameters: WorkflowContextValues[object],
    ) -> object:
        if len(parts) < 2:
            raise self._error_factory.create(reference)
        parameter_name = parts[1]
        parameter = parameters.find(parameter_name)
        if not parameter.present:
            raise self._error_factory.create(
                reference,
                f"parameter '{parameter_name}' not found in context",
            )
        return self._nested_values.resolve(
            parameter.value,
            parts[2:],
            reference,
        )

    def _resolve_named_value(
        self,
        parts: list[str],
        reference: str,
        values: WorkflowContextValues[Any],
    ) -> object:
        if len(parts) < 2:
            raise self._error_factory.create(reference)
        value = values.find(parts[1])
        if not value.present:
            raise self._error_factory.create(reference)
        return self._nested_values.resolve(
            value.value,
            parts[2:],
            reference,
        )
