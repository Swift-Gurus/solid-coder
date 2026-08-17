"""Parses workflow for-each references."""

from __future__ import annotations

from collections.abc import Mapping

from harness.for_each_reference_parsing import ForEachReferenceParsing
from harness.models import FlowValidationError
from harness.step_output_reference import StepOutputReference
from harness.step_output_reference_parsing import StepOutputReferenceParsing
from harness.step_output_reference_syntax_error import (
    StepOutputReferenceSyntaxError,
)
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: ForEachReferenceParser
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Parses and validates workflow for-each source-output expression syntax.
"""
class ForEachReferenceParser(ForEachReferenceParsing):
    def __init__(
        self,
        expression_parser: WorkflowExpressionParsing,
        reference_parser: StepOutputReferenceParsing,
    ) -> None:
        self._expression_parser = expression_parser
        self._reference_parser = reference_parser

    def parse(self, step_id: str, expression: object) -> StepOutputReference:
        if isinstance(expression, Mapping):
            source_step_id = expression.get("step_id")
            output_name = expression.get("output_name")
            if (
                isinstance(source_step_id, str)
                and source_step_id
                and isinstance(output_name, str)
                and output_name
            ):
                return StepOutputReference(
                    step_id=source_step_id,
                    output_name=output_name,
                )
            raise self._syntax_error(step_id)
        if not isinstance(expression, str):
            raise self._syntax_error(step_id)
        try:
            return self._reference_parser.parse(
                self._expression_parser.parse(expression).value
            )
        except (FlowValidationError, StepOutputReferenceSyntaxError) as error:
            raise self._syntax_error(step_id) from error

    def _syntax_error(self, step_id: str) -> FlowValidationError:
        return FlowValidationError(
            f"Step '{step_id}' for_each must use steps.<id>.outputs.<name>"
        )
