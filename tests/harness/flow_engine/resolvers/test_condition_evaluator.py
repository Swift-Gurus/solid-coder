"""Validates deterministic, type-strict evaluation of parsed workflow conditions."""

from __future__ import annotations

import sys
import unittest
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.all_condition import AllCondition  # noqa: E402
from harness.any_condition import AnyCondition  # noqa: E402
from harness.comparison_condition import ComparisonCondition  # noqa: E402
from harness.condition_comparator import ConditionComparator  # noqa: E402
from harness.condition_declaration_evaluator import ConditionDeclarationEvaluator  # noqa: E402
from harness.condition_evaluator import ConditionEvaluator  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.condition_reference_normalizer import ConditionReferenceNormalizer  # noqa: E402
from harness.condition_reference_resolver import ConditionReferenceResolver  # noqa: E402
from harness.condition_value_matcher import ConditionValueMatcher  # noqa: E402
from harness.interpolation_error import InterpolationError  # noqa: E402
from harness.not_condition import NotCondition  # noqa: E402


@dataclass(frozen=True)
class ResolvedExpression:
    reference: str
    value: Any


@dataclass
class StubExpressionEvaluator:
    resolved: tuple[ResolvedExpression, ...]
    evaluated: list[str] = field(default_factory=list)

    def evaluate(self, expression: str, context: dict[str, Any]) -> Any:
        self.evaluated.append(expression)
        for candidate in self.resolved:
            if candidate.reference == expression:
                return candidate.value
        raise InterpolationError(f"Unresolvable reference: '{expression}'")


class TestConditionEvaluator(unittest.TestCase):

    def test_equals_and_not_equals_are_type_strict(self) -> None:
        evaluator = StubExpressionEvaluator((ResolvedExpression("item.value", True),))
        sut = self._sut(evaluator)

        self.assertFalse(sut.evaluate(self._comparison(ConditionOperator.EQUALS, 1), {}))
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.NOT_EQUALS, 1), {}))
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.EQUALS, True), {}))

    def test_membership_is_type_strict(self) -> None:
        evaluator = StubExpressionEvaluator((ResolvedExpression("item.value", True),))
        sut = self._sut(evaluator)

        self.assertFalse(sut.evaluate(self._comparison(ConditionOperator.IN, [1, 2]), {}))
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.IN, [False, True]), {}))
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.NOT_IN, [1, 2]), {}))

    def test_exists_distinguishes_absent_from_present_null(self) -> None:
        present = self._sut(StubExpressionEvaluator((ResolvedExpression("item.value", None),)))
        absent = self._sut(StubExpressionEvaluator(()))

        self.assertTrue(present.evaluate(self._comparison(ConditionOperator.EXISTS, True), {}))
        self.assertFalse(present.evaluate(self._comparison(ConditionOperator.EXISTS, False), {}))
        self.assertFalse(absent.evaluate(self._comparison(ConditionOperator.EXISTS, True), {}))
        self.assertTrue(absent.evaluate(self._comparison(ConditionOperator.EXISTS, False), {}))

    def test_evaluates_nested_all_any_and_not_conditions(self) -> None:
        evaluator = StubExpressionEvaluator((
            ResolvedExpression("item.language", "swift"),
            ResolvedExpression("item.kind", "view"),
            ResolvedExpression("item.generated", False),
        ))
        sut = self._sut(evaluator)
        condition = AllCondition(conditions=(
            ComparisonCondition("{{item.language}}", ConditionOperator.EQUALS, "swift"),
            AnyCondition(conditions=(
                ComparisonCondition("{{item.kind}}", ConditionOperator.EQUALS, "view"),
                NotCondition(ComparisonCondition(
                    "{{item.generated}}",
                    ConditionOperator.EQUALS,
                    True,
                )),
            )),
        ))

        self.assertTrue(sut.evaluate(condition, {}))

    def test_composite_conditions_short_circuit(self) -> None:
        evaluator = StubExpressionEvaluator((ResolvedExpression("item.first", False),))
        sut = self._sut(evaluator)
        condition = AllCondition(conditions=(
            ComparisonCondition("{{item.first}}", ConditionOperator.EQUALS, True),
            ComparisonCondition("{{item.unreachable}}", ConditionOperator.EQUALS, True),
        ))

        self.assertFalse(sut.evaluate(condition, {}))
        self.assertEqual(evaluator.evaluated, ["item.first"])

    def _comparison(
        self,
        operator: ConditionOperator,
        expected: Any,
    ) -> ComparisonCondition:
        return ComparisonCondition(
            reference="{{item.value}}",
            operator=operator,
            expected=expected,
        )

    def _sut(self, expression_evaluator: StubExpressionEvaluator) -> ConditionEvaluator:
        reference_resolver = ConditionReferenceResolver(
            normalizer=ConditionReferenceNormalizer(),
            expression_evaluator=expression_evaluator,
        )
        comparison_runtime = ConditionComparator(
            reference_resolver=reference_resolver,
            value_matcher=ConditionValueMatcher(),
        )
        return ConditionEvaluator(
            declaration_evaluator=ConditionDeclarationEvaluator(),
            comparison_runtime=comparison_runtime,
        )


if __name__ == "__main__":
    unittest.main()
