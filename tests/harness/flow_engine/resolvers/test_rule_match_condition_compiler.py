"""Validates deterministic rule matcher compilation into workflow conditions."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from findings.review_unit_kind import ReviewUnitKind  # noqa: E402
from harness.all_condition import AllCondition  # noqa: E402
from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.rule_match_condition_compiler import RuleMatchConditionCompiler  # noqa: E402
from harness.rule_match_declaration import RuleMatchDeclaration  # noqa: E402
from harness.rule_selection import RuleSelection  # noqa: E402
from harness.rule_selection_condition_compiler import (  # noqa: E402
    RuleSelectionConditionCompiler,
)
from harness.workflow_expression import WorkflowExpression  # noqa: E402


class TestRuleMatchConditionCompiler(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = RuleMatchConditionCompiler(
            RuleSelectionConditionCompiler()
        )

    def test_empty_matcher_needs_no_runtime_condition(self) -> None:
        self.assertIsNone(self.sut.compile(RuleMatchDeclaration()))

    def test_compiles_every_match_dimension_with_exact_semantics(self) -> None:
        result = self.sut.compile(
            RuleMatchDeclaration(
                file_extensions=RuleSelection(
                    included=[".swift", ".py"],
                    excluded=[".md"],
                ),
                unit_kinds=RuleSelection(
                    included=[ReviewUnitKind.CLASS, ReviewUnitKind.STRUCT],
                    excluded=[ReviewUnitKind.FUNCTION],
                ),
                tags=RuleSelection(
                    included=["ui", "swiftui"],
                    excluded=["test", "generated"],
                ),
            )
        )

        self.assertEqual(
            result,
            AllCondition(conditions=(
                self._comparison(
                    "params.review_unit.applicability.file_extension",
                    ConditionOperator.IN,
                    [".swift", ".py"],
                ),
                self._comparison(
                    "params.review_unit.applicability.file_extension",
                    ConditionOperator.NOT_IN,
                    [".md"],
                ),
                self._comparison(
                    "params.review_unit.applicability.unit_kind",
                    ConditionOperator.IN,
                    ["class", "struct"],
                ),
                self._comparison(
                    "params.review_unit.applicability.unit_kind",
                    ConditionOperator.NOT_IN,
                    ["function"],
                ),
                self._comparison(
                    "params.review_unit.applicability.tags",
                    ConditionOperator.CONTAINS,
                    "ui",
                ),
                self._comparison(
                    "params.review_unit.applicability.tags",
                    ConditionOperator.CONTAINS,
                    "swiftui",
                ),
                self._comparison(
                    "params.review_unit.applicability.tags",
                    ConditionOperator.NOT_CONTAINS,
                    "test",
                ),
                self._comparison(
                    "params.review_unit.applicability.tags",
                    ConditionOperator.NOT_CONTAINS,
                    "generated",
                ),
            )),
        )

    def _comparison(
        self,
        reference: str,
        operator: ConditionOperator,
        expected: object,
    ) -> ComparisonCondition:
        return ComparisonCondition(
            reference=WorkflowExpression(reference),
            operator=operator,
            expected=expected,
        )


if __name__ == "__main__":
    unittest.main()
