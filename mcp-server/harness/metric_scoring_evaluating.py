"""Defines deterministic evaluation of one metric scoring declaration."""

from typing import Protocol

from findings.review_severity import ReviewSeverity
from harness.metric_scoring_band import MetricComparisonValue
from harness.metric_scoring_declaration import MetricScoringDeclaration


"""
solid-name: MetricScoringEvaluating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for evaluating a validated scalar metric value against deterministic severity bands.
"""
class MetricScoringEvaluating(Protocol):
    def evaluate(
        self,
        value: MetricComparisonValue,
        scoring: MetricScoringDeclaration,
    ) -> ReviewSeverity: ...
