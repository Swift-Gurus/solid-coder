"""Validates a workflow reference against a configured root."""

from harness.flow_validation_error import FlowValidationError
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_expression_parsing import WorkflowExpressionParsing

"""
solid-name: RootedReferencePathDecoder
solid-category: boundary
solid-spec: [SPEC-059]
solid-description: Parses a rooted workflow reference into validated field components at the input boundary.
"""


class RootedReferencePathDecoder(StructuredModelDecoding[list[str]]):
    def __init__(self, root: str, expression_parser: WorkflowExpressionParsing) -> None:
        self._root = root
        self._expression_parser = expression_parser

    def decode(self, value: object, description: str) -> list[str]:
        try:
            expression = self._expression_parser.parse(value)
        except FlowValidationError as error:
            raise FlowValidationError(f"{description}: {error}") from error
        components = expression.value.split(".")
        if components[0] != self._root or any(
            not component for component in components
        ):
            raise FlowValidationError(
                f"{description} must reference {self._root} or its fields"
            )
        return components[1:]
