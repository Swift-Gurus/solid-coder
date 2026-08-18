"""Selects authoritative severity from deterministic metric bands."""

from findings.review_severity import ReviewSeverity
from harness.metric_band_matcher import MetricBandMatcher
from harness.metric_scoring_band import MetricComparisonValue
from harness.metric_scoring_declaration import MetricScoringDeclaration
from harness.metric_scoring_evaluating import MetricScoringEvaluating


"""
solid-name: MetricScoringEvaluator
solid-category: service
solid-spec: [SPEC-039]
solid-description: Selects deterministic review severity from declared metric bands.
"""
class MetricScoringEvaluator(MetricScoringEvaluating):
    def __init__(self, band_matcher: MetricBandMatcher) -> None:
        self._band_matcher = band_matcher

    def evaluate(
        self,
        value: MetricComparisonValue,
        scoring: MetricScoringDeclaration,
    ) -> ReviewSeverity:
        if scoring.severe is not None and self._band_matcher.matches(
            value,
            scoring.severe,
        ):
            return ReviewSeverity.SEVERE
        if scoring.minor is not None and self._band_matcher.matches(
            value,
            scoring.minor,
        ):
            return ReviewSeverity.MINOR
        return ReviewSeverity.COMPLIANT
