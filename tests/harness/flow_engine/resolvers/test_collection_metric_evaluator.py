"""Tests deterministic collection metric evaluation semantics."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock

sys.path.insert(0, str(Path(__file__).resolve().parents[4] / "mcp-server"))

from harness.all_condition import AllCondition
from harness.any_condition import AnyCondition
from harness.builtin_attribute_reader import BuiltinAttributeReader
from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.collection_metric_evaluator_factory import (
    CollectionMetricEvaluatorFactory,
)
from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducer_type import CollectionMetricReducerType
from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator
from harness.expression_resolver import ExpressionResolver
from harness.flow_engine_assembly_factory import FlowEngineAssemblyFactory
from harness.flow_validation_error import FlowValidationError
from harness.flow_validation_error_factory import FlowValidationErrorFactory
from harness.interpolation_error_factory import InterpolationErrorFactory
from harness.nested_component_accessor import NestedComponentAccessor
from harness.nested_path_resolver import NestedPathResolver
from harness.not_condition import NotCondition
from harness.step_output_reference import StepOutputReference
from harness.strict_value_comparator import StrictValueComparator
from harness.workflow_expression import WorkflowExpression
from harness.workflow_results_visibility_selector import (
    WorkflowResultsVisibilitySelector,
)
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolver import WorkflowStepContextResolver


"""
solid-name: TestCollectionMetricEvaluator
solid-category: unit-test
solid-spec: [SPEC-053]
solid-description: Verifies ordered filtered-count semantics for collection-backed metrics.
"""
class TestCollectionMetricEvaluator(unittest.TestCase):
    def setUp(self) -> None:
        interpolation_errors = InterpolationErrorFactory()
        condition_evaluator = FlowEngineAssemblyFactory().build().condition_evaluator
        nested_value_resolver = NestedPathResolver(
            component_accessor=NestedComponentAccessor(
                attribute_reader=BuiltinAttributeReader()
            ),
            error_factory=interpolation_errors,
        )
        expression_evaluator = ExpressionResolver(
                step_output_resolver=Mock(),
                nested_value_resolver=nested_value_resolver,
                error_factory=interpolation_errors,
            )
        self.sut = CollectionMetricEvaluatorFactory().build(
            condition_evaluator=condition_evaluator,
            expression_evaluator=expression_evaluator,
            nested_value_resolver=nested_value_resolver,
            value_comparator=StrictValueComparator(),
            context_resolver=WorkflowStepContextResolver(
                WorkflowResultsVisibilitySelector()
            ),
            error_factory=FlowValidationErrorFactory(),
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

    def test_maximum_projects_filtered_numeric_values(self) -> None:
        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                condition=ComparisonCondition(
                    reference=WorkflowExpression("item.is_exception"),
                    operator=ConditionOperator.EQUALS,
                    expected=False,
                ),
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.MAXIMUM,
                    value=WorkflowExpression("item.depth"),
                ),
            ),
            [
                {"depth": 2, "is_exception": False},
                {"depth": 9, "is_exception": True},
                {"depth": 5, "is_exception": False},
            ],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 5)
        self.assertEqual(
            [(evidence.index, evidence.value) for evidence in result.projection_evidence],
            [(0, 2), (2, 5)],
        )

    def test_minimum_preserves_numeric_result(self) -> None:
        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.MINIMUM,
                    value=WorkflowExpression("item.coverage"),
                ),
            ),
            [{"coverage": 0.8}, {"coverage": 0.5}, {"coverage": 1.0}],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 0.5)

    def test_distinct_count_uses_strict_scalar_identity_and_first_indexes(self) -> None:
        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.DISTINCT_COUNT,
                    value=WorkflowExpression("item.value"),
                ),
            ),
            [{"value": 1}, {"value": True}, {"value": 1}, {"value": "1"}],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 3)
        self.assertEqual(result.distinct_indexes, [0, 1, 3])

    def test_ratio_uses_only_outer_filtered_entries(self) -> None:
        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                condition=ComparisonCondition(
                    reference=WorkflowExpression("item.include"),
                    operator=ConditionOperator.EQUALS,
                    expected=True,
                ),
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.RATIO,
                    numerator_condition=AllCondition(conditions=(
                        ComparisonCondition(
                            reference=WorkflowExpression("item.classification"),
                            operator=ConditionOperator.EQUALS,
                            expected="UNSAFE",
                        ),
                        ComparisonCondition(
                            reference=WorkflowExpression("item.is_exception"),
                            operator=ConditionOperator.EQUALS,
                            expected=False,
                        ),
                    )),
                    denominator_condition=ComparisonCondition(
                        reference=WorkflowExpression("item.is_exception"),
                        operator=ConditionOperator.EQUALS,
                        expected=False,
                    ),
                ),
            ),
            [
                {"include": True, "classification": "UNSAFE", "is_exception": False},
                {"include": True, "classification": "SAFE", "is_exception": False},
                {"include": False, "classification": "UNSAFE", "is_exception": False},
                {"include": True, "classification": "UNSAFE", "is_exception": True},
            ],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 0.5)
        self.assertEqual(result.numerator_indexes, [0])
        self.assertEqual(result.denominator_indexes, [0, 1])

    def test_ratio_with_zero_denominator_returns_zero(self) -> None:
        condition = ComparisonCondition(
            reference=WorkflowExpression("item.selected"),
            operator=ConditionOperator.EQUALS,
            expected=True,
        )

        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.RATIO,
                    numerator_condition=condition,
                    denominator_condition=condition,
                ),
            ),
            [{"selected": False}],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 0.0)
        self.assertTrue(result.zero_denominator)

    def test_ratio_with_zero_denominator_uses_authored_empty_value(self) -> None:
        condition = ComparisonCondition(
            reference=WorkflowExpression("item.selected"),
            operator=ConditionOperator.EQUALS,
            expected=True,
        )

        result = self.sut.evaluate(
            CollectionMetricCalculation(
                source=self.source,
                reducer=CollectionMetricReducer(
                    type=CollectionMetricReducerType.RATIO,
                    empty_value=1.0,
                    numerator_condition=condition,
                    denominator_condition=condition,
                ),
            ),
            [],
            WorkflowRunContext(),
        )

        self.assertEqual(result.value, 1.0)
        self.assertTrue(result.zero_denominator)

    def test_maximum_rejects_an_empty_filtered_collection(self) -> None:
        with self.assertRaisesRegex(
            FlowValidationError,
            "maximum reducer cannot reduce an empty collection",
        ):
            self.sut.evaluate(
                CollectionMetricCalculation(
                    source=self.source,
                    reducer=CollectionMetricReducer(
                        type=CollectionMetricReducerType.MAXIMUM,
                        value=WorkflowExpression("item.depth"),
                    ),
                ),
                [],
                WorkflowRunContext(),
            )


if __name__ == "__main__":
    unittest.main()
