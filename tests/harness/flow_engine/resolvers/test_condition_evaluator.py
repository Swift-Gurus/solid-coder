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
from harness.condition_evidence import (  # noqa: E402
    ComparisonConditionEvidence,
    CompositeConditionEvidence,
)
from harness.condition_comparator import ConditionComparator  # noqa: E402
from harness.condition_declaration_evaluator import ConditionDeclarationEvaluator  # noqa: E402
from harness.condition_evaluator import ConditionEvaluator  # noqa: E402
from harness.condition_operator import ConditionOperator  # noqa: E402
from harness.condition_reference_resolver import ConditionReferenceResolver  # noqa: E402
from harness.condition_value_matcher import ConditionValueMatcher  # noqa: E402
from harness.interpolation_error import InterpolationError  # noqa: E402
from harness.not_condition import NotCondition  # noqa: E402
from harness.resolved_condition_value import ResolvedConditionValue  # noqa: E402
from harness.strict_collection_value_matcher import (  # noqa: E402
    StrictCollectionValueMatcher,
)
from harness.strict_value_comparator import StrictValueComparator  # noqa: E402
from harness.workflow_run_context import WorkflowRunContext  # noqa: E402
from harness.workflow_expression import WorkflowExpression  # noqa: E402


_CONTEXT = WorkflowRunContext()


@dataclass(frozen=True)
class ResolvedExpression:
    reference: str
    value: Any


@dataclass
class StubExpressionEvaluator:
    resolved: tuple[ResolvedExpression, ...]
    evaluated: list[str] = field(default_factory=list)

    def evaluate(self, expression: str, context: WorkflowRunContext) -> Any:
        self.evaluated.append(expression)
        for candidate in self.resolved:
            if candidate.reference == expression:
                return candidate.value
        raise InterpolationError(f"Unresolvable reference: '{expression}'")


class TestConditionEvaluator(unittest.TestCase):

    def test_returns_typed_nested_evidence_for_a_decision(self) -> None:
        sut = self._sut(StubExpressionEvaluator((
            ResolvedExpression("item.language", "kotlin"),
        )))
        condition = AllCondition(conditions=(
            ComparisonCondition(
                WorkflowExpression("item.language"),
                ConditionOperator.EQUALS,
                "swift",
            ),
            ComparisonCondition(
                WorkflowExpression("item.kind"),
                ConditionOperator.EQUALS,
                "view",
            ),
        ))

        evidence = sut.evaluate(condition, _CONTEXT)

        self.assertEqual(
            evidence,
            CompositeConditionEvidence(
                kind="all",
                matched=False,
                children=[
                    ComparisonConditionEvidence(
                        reference="item.language",
                        operator=ConditionOperator.EQUALS,
                        expected="swift",
                        actual=ResolvedConditionValue(
                            present=True,
                            value="kotlin",
                        ),
                        matched=False,
                    )
                ],
            ),
        )

    def test_equals_and_not_equals_are_type_strict(self) -> None:
        evaluator = StubExpressionEvaluator((ResolvedExpression("item.value", True),))
        sut = self._sut(evaluator)

        self.assertFalse(sut.evaluate(self._comparison(ConditionOperator.EQUALS, 1), _CONTEXT).matched)
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.NOT_EQUALS, 1), _CONTEXT).matched)
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.EQUALS, True), _CONTEXT).matched)

    def test_membership_is_type_strict(self) -> None:
        evaluator = StubExpressionEvaluator((ResolvedExpression("item.value", True),))
        sut = self._sut(evaluator)

        self.assertFalse(sut.evaluate(self._comparison(ConditionOperator.IN, [1, 2]), _CONTEXT).matched)
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.IN, [False, True]), _CONTEXT).matched)
        self.assertTrue(sut.evaluate(self._comparison(ConditionOperator.NOT_IN, [1, 2]), _CONTEXT).matched)

    def test_collection_containment_is_type_strict(self) -> None:
        evaluator = StubExpressionEvaluator((
            ResolvedExpression("item.value", ["swiftui", True]),
        ))
        sut = self._sut(evaluator)

        self.assertTrue(
            sut.evaluate(
                self._comparison(ConditionOperator.CONTAINS, "swiftui"),
                _CONTEXT,
            ).matched
        )
        self.assertFalse(
            sut.evaluate(
                self._comparison(ConditionOperator.CONTAINS, 1),
                _CONTEXT,
            ).matched
        )
        self.assertTrue(
            sut.evaluate(
                self._comparison(ConditionOperator.NOT_CONTAINS, "generated"),
                _CONTEXT,
            ).matched
        )

    def test_exists_distinguishes_absent_from_present_null(self) -> None:
        present = self._sut(StubExpressionEvaluator((ResolvedExpression("item.value", None),)))
        absent = self._sut(StubExpressionEvaluator(()))

        self.assertTrue(present.evaluate(self._comparison(ConditionOperator.EXISTS, True), _CONTEXT).matched)
        self.assertFalse(present.evaluate(self._comparison(ConditionOperator.EXISTS, False), _CONTEXT).matched)
        self.assertFalse(absent.evaluate(self._comparison(ConditionOperator.EXISTS, True), _CONTEXT).matched)
        self.assertTrue(absent.evaluate(self._comparison(ConditionOperator.EXISTS, False), _CONTEXT).matched)

    def test_evaluates_nested_all_any_and_not_conditions(self) -> None:
        evaluator = StubExpressionEvaluator((
            ResolvedExpression("item.language", "swift"),
            ResolvedExpression("item.kind", "view"),
            ResolvedExpression("item.generated", False),
        ))
        sut = self._sut(evaluator)
        condition = AllCondition(conditions=(
            ComparisonCondition(WorkflowExpression("item.language"), ConditionOperator.EQUALS, "swift"),
            AnyCondition(conditions=(
                ComparisonCondition(WorkflowExpression("item.kind"), ConditionOperator.EQUALS, "view"),
                NotCondition(ComparisonCondition(
                    WorkflowExpression("item.generated"),
                    ConditionOperator.EQUALS,
                    True,
                )),
            )),
        ))

        self.assertTrue(sut.evaluate(condition, _CONTEXT).matched)

    def test_composite_conditions_short_circuit(self) -> None:
        evaluator = StubExpressionEvaluator((ResolvedExpression("item.first", False),))
        sut = self._sut(evaluator)
        condition = AllCondition(conditions=(
            ComparisonCondition(WorkflowExpression("item.first"), ConditionOperator.EQUALS, True),
            ComparisonCondition(WorkflowExpression("item.unreachable"), ConditionOperator.EQUALS, True),
        ))

        self.assertFalse(sut.evaluate(condition, _CONTEXT).matched)
        self.assertEqual(evaluator.evaluated, ["item.first"])

    def _comparison(
        self,
        operator: ConditionOperator,
        expected: Any,
    ) -> ComparisonCondition:
        return ComparisonCondition(
            reference=WorkflowExpression(value="item.value"),
            operator=operator,
            expected=expected,
        )

    def _sut(self, expression_evaluator: StubExpressionEvaluator) -> ConditionEvaluator:
        comparator = StrictValueComparator()
        reference_resolver = ConditionReferenceResolver(
            expression_evaluator=expression_evaluator,
        )
        comparison_runtime = ConditionComparator(
            reference_resolver=reference_resolver,
            value_matcher=ConditionValueMatcher(
                comparator=comparator,
                collection_matcher=StrictCollectionValueMatcher(comparator),
            ),
        )
        return ConditionEvaluator(
            declaration_evaluator=ConditionDeclarationEvaluator(),
            comparison_runtime=comparison_runtime,
        )


if __name__ == "__main__":
    unittest.main()
