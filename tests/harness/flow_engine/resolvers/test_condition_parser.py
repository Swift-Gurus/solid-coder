"""Validates parsing declarative workflow conditions into sealed runtime models."""

from __future__ import annotations

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.all_condition import AllCondition  # noqa: E402
from harness.any_condition import AnyCondition  # noqa: E402
from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.comparison_condition_parser import ComparisonConditionParser  # noqa: E402
from harness.composition_condition_parser import CompositionConditionParser  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.condition_parser import ConditionParser  # noqa: E402
from harness.models import FlowValidationError  # noqa: E402
from harness.not_condition import NotCondition  # noqa: E402


class TestConditionParser(unittest.TestCase):

    def setUp(self) -> None:
        self.sut = ConditionParser(
            composition_parser=CompositionConditionParser(),
            comparison_parser=ComparisonConditionParser(),
        )

    def test_parses_each_leaf_operator(self) -> None:
        cases = [
            ("equals", "swift", ConditionOperator.EQUALS),
            ("not_equals", "swift", ConditionOperator.NOT_EQUALS),
            ("in", ["swift", "python"], ConditionOperator.IN),
            ("not_in", ["view", "test"], ConditionOperator.NOT_IN),
            ("exists", True, ConditionOperator.EXISTS),
        ]

        for key, expected, operator in cases:
            with self.subTest(operator=key):
                parsed = self.sut.parse({"ref": "{{item.language}}", key: expected})

                self.assertEqual(
                    parsed,
                    ComparisonCondition(
                        reference="{{item.language}}",
                        operator=operator,
                        expected=expected,
                    ),
                )

    def test_parses_nested_composition(self) -> None:
        parsed = self.sut.parse({
            "all": [
                {"ref": "{{item.language}}", "equals": "swift"},
                {"any": [
                    {"ref": "{{item.unit_kind}}", "equals": "view"},
                    {"not": {"ref": "{{item.generated}}", "equals": True}},
                ]},
            ],
        })

        self.assertEqual(
            parsed,
            AllCondition(conditions=(
                ComparisonCondition(
                    reference="{{item.language}}",
                    operator=ConditionOperator.EQUALS,
                    expected="swift",
                ),
                AnyCondition(conditions=(
                    ComparisonCondition(
                        reference="{{item.unit_kind}}",
                        operator=ConditionOperator.EQUALS,
                        expected="view",
                    ),
                    NotCondition(condition=ComparisonCondition(
                        reference="{{item.generated}}",
                        operator=ConditionOperator.EQUALS,
                        expected=True,
                    )),
                )),
            )),
        )

    def test_rejects_leaf_with_multiple_operators(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "exactly one comparison operator"):
            self.sut.parse({
                "ref": "{{item.language}}",
                "equals": "swift",
                "not_equals": "python",
            })

    def test_rejects_empty_composition(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "non-empty condition list"):
            self.sut.parse({"all": []})

    def test_rejects_membership_value_that_is_not_an_array(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "must use an array comparison value"):
            self.sut.parse({"ref": "{{item.language}}", "in": "swift"})

    def test_rejects_exists_value_that_is_not_boolean(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "exists comparison must be boolean"):
            self.sut.parse({"ref": "{{item.language}}", "exists": "yes"})

    def test_rejects_unknown_or_extra_fields(self) -> None:
        with self.assertRaisesRegex(FlowValidationError, "unsupported condition fields"):
            self.sut.parse({
                "ref": "{{item.language}}",
                "equals": "swift",
                "case_sensitive": False,
            })


if __name__ == "__main__":
    unittest.main()
