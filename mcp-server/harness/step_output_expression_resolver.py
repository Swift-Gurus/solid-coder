"""Resolves workflow step-output expressions."""

from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.interpolation_error_creating import InterpolationErrorCreating
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: StepOutputExpressionResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Resolves a workflow expression to one recorded step output.
"""
class StepOutputExpressionResolver(ExpressionEvaluating):
    def __init__(self, error_factory: InterpolationErrorCreating) -> None:
        self._error_factory = error_factory

    def evaluate(self, expr: str, context: WorkflowRunContext) -> Any:
        parts = expr.split(".")
        if len(parts) < 4 or parts[0] != "steps" or parts[2] != "outputs":
            raise self._error_factory.create(expr)
        step_id = parts[1]
        output_name = parts[3]
        completed_step = context.completed_steps.find(step_id)
        if not completed_step.present or completed_step.value is None:
            raise self._error_factory.create(expr)
        value = completed_step.value.get(output_name)
        if value is None:
            raise self._error_factory.create(expr)
        return value
