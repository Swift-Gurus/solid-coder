"""Tests deterministic collection metric evaluation semantics."""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.all_condition import AllCondition
from harness.any_condition import AnyCondition
from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.collection_metric_evaluator import CollectionMetricEvaluator
from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.not_condition import NotCondition
from harness.step_output_reference import StepOutputReference
from harness.workflow_expression import WorkflowExpression
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: TestCollectionMetricEvaluator
solid-category: unit-test
solid-spec: [SPEC-053]
solid-description: Verifies ordered filtered-count semantics for collection-backed metrics.
"""
class TestCollectionMetricEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        self.sut = CollectionMetricEvaluator(
            FlowEngineAssemblyFactory().build().condition_evaluator
        )
        self.source = StepOutputReference(
            step_id="analyze",
            output_name="entries",
        )

    def test_counts_every_source_index_when_condition_is_omitted(self) -> None:
        duplicated = {"name": "same"}

        result = self.sut.evaluate(
            CollectionMetricCalculation(source=self.source),
            [duplicated, duplicated],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 2)
        self.assertEqual(result.matched_indexes, [0, 1])
        self.assertEqual(result.excluded_indexes, [])

    def test_counts_only_entries_matching_every_authored_comparison(self) -> None:
        condition = AllCondition(conditions=(
            ComparisonCondition(
                reference=WorkflowExpression("item.classification"),
                operator=ConditionOperator.EQUALS,
                expected="DETACHED",
            ),
            ComparisonCondition(
                reference=WorkflowExpression("item.is_exception"),
                operator=ConditionOperator.EQUALS,
                expected=False,
            ),
        ))

        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                condition=condition,
            ),
            [
                {"classification": "DETACHED", "is_exception": False},
                {"classification": "STRUCTURED", "is_exception": False},
                {"classification": "DETACHED", "is_exception": True},
            ],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 1)
        self.assertEqual(result.matched_indexes, [0])
        self.assertEqual(result.excluded_indexes, [1, 2])
        self.assertEqual(len(result.condition_evidence), 3)

    def test_empty_collection_returns_zero(self) -> None:
        result = self.sut.evaluate(
            CollectionMetricCalculation(source=self.source),
            [],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 0)
        self.assertEqual(result.source_size, 0)

    def test_reuses_nested_any_and_not_condition_semantics(self) -> None:
        condition = AnyCondition(conditions=(
            ComparisonCondition(
                reference=WorkflowExpression("item.classification"),
                operator=ConditionOperator.EQUALS,
                expected="STRUCTURED",
            ),
            NotCondition(
                condition=ComparisonCondition(
                    reference=WorkflowExpression("item.is_exception"),
                    operator=ConditionOperator.EQUALS,
                    expected=True,
                )
            ),
        ))

        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                condition=condition,
            ),
            [
                {"classification": "DETACHED", "is_exception": False},
                {"classification": "DETACHED", "is_exception": True},
                {"classification": "STRUCTURED", "is_exception": True},
            ],
            WorkflowRunContext(),
        )

        self.assertEqual(result.matched_indexes, [0, 2])
        self.assertEqual(result.excluded_indexes, [1])

    def test_filters_client_authored_field_names_without_registration(self) -> None:
        condition = AllCondition(conditions=(
            ComparisonCondition(
                reference=WorkflowExpression("item.name"),
                operator=ConditionOperator.EQUALS,
                expected="this",
            ),
            ComparisonCondition(
                reference=WorkflowExpression("item.exempt"),
                operator=ConditionOperator.EQUALS,
                expected=False,
            ),
        ))

        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                condition=condition,
            ),
            [
                {"name": "this", "exempt": False},
                {"name": "other", "exempt": False},
                {"name": "this", "exempt": True},
            ],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 1)
        self.assertEqual(result.matched_indexes, [0])


if __name__ == "__main__":
    unittest.main()
