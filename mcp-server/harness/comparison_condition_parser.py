"""Parses workflow comparison condition declarations."""

from __future__ import annotations

from collections.abc import Mapping

from harness.comparison_condition import ComparisonCondition
from harness.condition_declaration import ConditionDeclaration
from harness.condition_node_parsing import ConditionNodeParsing
from harness.condition_operator import ConditionOperator
from harness.condition_parsing import ConditionParsing
from harness.models import FlowValidationError


"""
solid-name: ComparisonConditionParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Maps comparison condition input into a typed condition declaration.
"""
class ComparisonConditionParser(ConditionNodeParsing):
    _OPERATORS = frozenset(operator.value for operator in ConditionOperator)

    def parse(
        self,
        raw: Mapping[object, object],
        nested_parser: ConditionParsing,
    ) -> ConditionDeclaration:
        reference = raw.get("ref")
        if not isinstance(reference, str) or not reference.strip():
            raise FlowValidationError(
                "Workflow comparison condition must declare a non-empty ref"
            )
        operators = self._OPERATORS.intersection(raw.keys())
        if len(operators) != 1:
            raise FlowValidationError(
                "Workflow comparison condition must declare exactly one comparison operator"
            )
        unsupported = set(raw.keys()).difference({"ref", *self._OPERATORS})
        if unsupported:
            raise FlowValidationError("Workflow condition has unsupported condition fields")

        operator = ConditionOperator(next(iter(operators)))
        expected = raw[operator.value]
        if operator in (ConditionOperator.IN, ConditionOperator.NOT_IN):
            if not isinstance(expected, list):
                raise FlowValidationError(
                    f"Workflow condition '{operator.value}' must use an array comparison value"
                )
        if operator is ConditionOperator.EXISTS and not isinstance(expected, bool):
            raise FlowValidationError(
                "Workflow condition exists comparison must be boolean"
            )
        return ComparisonCondition(
            reference=reference,
            operator=operator,
            expected=expected,
        )
