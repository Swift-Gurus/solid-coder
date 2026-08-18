"""Compares validated scalar metric values with deterministic scoring bands."""

from harness.metric_scoring_band import MetricComparisonValue, MetricScoringBand
from harness.scoring_comparison_operator import ScoringComparisonOperator


"""
solid-name: MetricBandMatcher
solid-category: service
solid-spec: [SPEC-039]
solid-description: Applies the closed scoring comparison vocabulary to one scalar value and band.
"""
class MetricBandMatcher:
    def matches(
        self,
        value: MetricComparisonValue,
        band: MetricScoringBand,
    ) -> bool:
        if band.operator == ScoringComparisonOperator.EQUALS:
            return value == band.value
        if band.operator == ScoringComparisonOperator.NOT_EQUALS:
            return value != band.value
        if band.operator == ScoringComparisonOperator.GREATER_THAN:
            return value > band.value
        if band.operator == ScoringComparisonOperator.GREATER_THAN_OR_EQUAL:
            return value >= band.value
        if band.operator == ScoringComparisonOperator.LESS_THAN:
            return value < band.value
        if band.operator == ScoringComparisonOperator.LESS_THAN_OR_EQUAL:
            return value <= band.value
        raise ValueError(f"Unsupported scoring operator '{band.operator.value}'")
