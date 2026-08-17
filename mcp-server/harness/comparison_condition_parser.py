"""Parses workflow comparison condition declarations."""

from __future__ import annotations

from collections.abc import Mapping

from harness.comparison_condition import ComparisonCondition
from harness.comparison_operation_parsing import ComparisonOperationParsing
from harness.condition_declaration import ConditionDeclaration
from harness.condition_node_parsing import ConditionNodeParsing
from harness.condition_parsing import ConditionParsing
from harness.workflow_expression_parsing import WorkflowExpressionParsing


"""
solid-name: ComparisonConditionParser
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Maps comparison condition input into a typed condition declaration.
"""
class ComparisonConditionParser(ConditionNodeParsing):

    def __init__(
        self,
        expression_parser: WorkflowExpressionParsing,
        operation_parser: ComparisonOperationParsing,
    ) -> None:
        self._expression_parser = expression_parser
        self._operation_parser = operation_parser

    def parse(
        self,
        raw: Mapping[object, object],
        nested_parser: ConditionParsing,
    ) -> ConditionDeclaration:
        operation = self._operation_parser.parse(raw)
        return ComparisonCondition(
            reference=self._expression_parser.parse(raw.get("ref")),
            operator=operation.operator,
            expected=operation.expected,
        )
