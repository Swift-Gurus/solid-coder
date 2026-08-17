"""Resolves workflow step-output expressions."""

from __future__ import annotations

from typing import Any

from harness.expression_evaluating import ExpressionEvaluating
from harness.interpolation_error_creating import InterpolationErrorCreating
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.step_output_reference_resolving import StepOutputReferenceResolving
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: StepOutputExpressionResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Resolves a workflow expression to one recorded step output.
"""
class StepOutputExpressionResolver(ExpressionEvaluating):
    def __init__(
        self,
        reference_parser: StepOutputReferenceParsing,
        reference_resolver: StepOutputReferenceResolving,
        error_factory: InterpolationErrorCreating,
    ) -> None:
        self._reference_parser = reference_parser
        self._reference_resolver = reference_resolver
        self._error_factory = error_factory

    def evaluate(self, expr: str, context: WorkflowRunContext) -> Any:
        try:
            reference = self._reference_parser.parse(expr)
        except StepOutputReferenceSyntaxError as error:
            raise self._error_factory.create(expr) from error
        return self._reference_resolver.resolve(reference, context)
