"""Calculates a ratio from filtered collection metric observations."""

from harness.collection_metric_reducer import CollectionMetricReducer
from harness.collection_metric_reducing import CollectionMetricReducing
from harness.collection_metric_reduction_result import (
    CollectionMetricReductionResult,
)
from harness.condition_decision_evaluating import ConditionDecisionEvaluating
from harness.flow_validation_error_creating import FlowValidationErrorCreating
from harness.ratio_value_calculator import RatioValueCalculator
from harness.selected_collection_metric_entry import SelectedCollectionMetricEntry

"""
solid-name: RatioCollectionMetricReducer
solid-category: strategy
solid-spec: [SPEC-054]
solid-description: Calculates an auditable numerator-to-denominator ratio from validated observation conditions.
"""


class RatioCollectionMetricReducer(CollectionMetricReducing):
    def __init__(
        self,
        condition_evaluator: ConditionDecisionEvaluating,
        value_calculator: RatioValueCalculator,
        error_factory: FlowValidationErrorCreating,
    ) -> None:
        self._condition_evaluator = condition_evaluator
        self._value_calculator = value_calculator
        self._error_factory = error_factory

    def reduce(
        self,
        declaration: CollectionMetricReducer,
        entries: list[SelectedCollectionMetricEntry],
    ) -> CollectionMetricReductionResult:
        numerator_condition = declaration.numerator_condition
        denominator_condition = declaration.denominator_condition
        if numerator_condition is None or denominator_condition is None:
            raise self._error_factory.create(
                "Ratio reducer requires numerator and denominator conditions"
            )
        numerator_indexes: list[int] = []
        denominator_indexes: list[int] = []
        numerator_evidence = []
        denominator_evidence = []
        for entry in entries:
            numerator = self._condition_evaluator.evaluate(
                numerator_condition,
                entry.context,
            )
            denominator = self._condition_evaluator.evaluate(
                denominator_condition,
                entry.context,
            )
            numerator_evidence.append(numerator)
            denominator_evidence.append(denominator)
            if numerator.matched:
                numerator_indexes.append(entry.source_index)
            if denominator.matched:
                denominator_indexes.append(entry.source_index)
        zero_denominator = not denominator_indexes
        return CollectionMetricReductionResult(
            value=self._value_calculator.calculate(
                numerator_count=len(numerator_indexes),
                denominator_count=len(denominator_indexes),
                empty_value=(
                    declaration.empty_value
                    if declaration.empty_value is not None
                    else 0.0
                ),
            ),
            numerator_indexes=numerator_indexes,
            denominator_indexes=denominator_indexes,
            numerator_condition_evidence=numerator_evidence,
            denominator_condition_evidence=denominator_evidence,
            zero_denominator=zero_denominator,
        )
