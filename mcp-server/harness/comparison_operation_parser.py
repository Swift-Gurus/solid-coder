"""Parses workflow comparison operator declarations."""

from collections.abc import Mapping

from harness.comparison_operation import ComparisonOperation
from harness.comparison_operation_parsing import ComparisonOperationParsing
from harness.condition_operator import ConditionOperator
from harness.flow_validation_error_creating import FlowValidationErrorCreating


"""
solid-name: ComparisonOperationParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Validates and parses workflow comparison operators and expected values.
"""
class ComparisonOperationParser(ComparisonOperationParsing):
    _OPERATORS = frozenset(operator.value for operator in ConditionOperator)

    def __init__(self, error_factory: FlowValidationErrorCreating) -> None:
        self._error_factory = error_factory

    def parse(self, raw: Mapping[object, object]) -> ComparisonOperation:
        operators = self._OPERATORS.intersection(raw.keys())
        if len(operators) != 1:
            raise self._error_factory.create(
                "Workflow comparison condition must declare exactly one comparison operator"
            )
        unsupported = set(raw.keys()).difference({"ref", *self._OPERATORS})
        if unsupported:
            raise self._error_factory.create(
                "Workflow condition has unsupported condition fields"
            )

        operator = ConditionOperator(next(iter(operators)))
        expected = raw[operator.value]
        if operator in (ConditionOperator.IN, ConditionOperator.NOT_IN):
            if not isinstance(expected, list):
                raise self._error_factory.create(
                    f"Workflow condition '{operator.value}' must use an array comparison value"
                )
        if operator is ConditionOperator.EXISTS and not isinstance(expected, bool):
            raise self._error_factory.create(
                "Workflow condition exists comparison must be boolean"
            )
        return ComparisonOperation(operator=operator, expected=expected)
