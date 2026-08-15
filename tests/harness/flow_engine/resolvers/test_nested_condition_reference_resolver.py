"""Validates nested item and parameter references used by workflow conditions."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.expression_resolver import ExpressionResolver  # noqa: E402
from harness.builtin_attribute_reader import BuiltinAttributeReader  # noqa: E402
from harness.interpolation_error import InterpolationError  # noqa: E402
from harness.interpolation_error_factory import InterpolationErrorFactory  # noqa: E402
from harness.nested_component_accessor import NestedComponentAccessor  # noqa: E402
from harness.nested_path_resolver import NestedPathResolver  # noqa: E402
from harness.step_output_expression_resolver import StepOutputExpressionResolver  # noqa: E402


@dataclass(frozen=True)
class ReviewUnit:
    language: str
    unit_kind: str


class TestNestedConditionReferenceResolver(unittest.TestCase):

    def setUp(self) -> None:
        error_factory = InterpolationErrorFactory()
        nested_values = NestedPathResolver(
            component_accessor=NestedComponentAccessor(
                attribute_reader=BuiltinAttributeReader()
            ),
            error_factory=error_factory,
        )
        self.sut = ExpressionResolver(
            step_output_resolver=StepOutputExpressionResolver(error_factory),
            nested_value_resolver=nested_values,
            error_factory=error_factory,
        )

    def test_resolves_nested_item_mapping_path(self) -> None:
        value = self.sut.evaluate(
            "item.language",
            {"item": {"language": "swift", "unit_kind": "view"}},
        )

        self.assertEqual(value, "swift")

    def test_resolves_nested_parameter_mapping_path(self) -> None:
        value = self.sut.evaluate(
            "params.review_unit.unit_kind",
            {"params": {"review_unit": {"language": "swift", "unit_kind": "view"}}},
        )

        self.assertEqual(value, "view")

    def test_resolves_nested_object_attribute_path(self) -> None:
        value = self.sut.evaluate(
            "params.review_unit.language",
            {"params": {"review_unit": ReviewUnit(language="swift", unit_kind="view")}},
        )

        self.assertEqual(value, "swift")

    def test_returns_present_null_value(self) -> None:
        value = self.sut.evaluate("item.language", {"item": {"language": None}})

        self.assertIsNone(value)

    def test_missing_nested_path_raises_actionable_error(self) -> None:
        with self.assertRaisesRegex(
            InterpolationError,
            "Unresolvable reference: 'item.language'",
        ):
            self.sut.evaluate("item.language", {"item": {"unit_kind": "view"}})


if __name__ == "__main__":
    unittest.main()
