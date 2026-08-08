"""Applies configured principle rules to immutable reviewed units."""

from dataclasses import replace

from findings.review_severity import ReviewSeverity
from findings.review_unit import ReviewUnit
from findings.review_violation import ReviewViolation
from scoring.principle_scorer_resolving import PrincipleScorerResolving
from scoring.review_unit_scoring import ReviewUnitScoring
from scoring.review_unit_scoring_result import ReviewUnitScoringResult


"""
solid-name: ReviewUnitScorer
solid-category: service
solid-description: Produces server-authoritative rule violations for one immutable reviewed code unit.
"""
class ReviewUnitScorer(ReviewUnitScoring):
    def __init__(self, scorer_resolver: PrincipleScorerResolving) -> None:
        self._scorer_resolver = scorer_resolver

    def score(self, unit: ReviewUnit, file_path: str) -> ReviewUnitScoringResult:
        violations: list[ReviewViolation] = []
        for principle_metrics in unit.metrics:
            resolution = self._scorer_resolver.resolve(
                principle_metrics.principle
            )
            if not resolution.succeeded or resolution.scorer is None:
                return ReviewUnitScoringResult(
                    error_message=(
                        f"{file_path}, unit {unit.name}: "
                        f"{resolution.error_message or 'scorer resolution failed'}"
                    )
                )

            for metric_id in resolution.scorer.metric_ids.identifiers:
                result = resolution.scorer.score(
                    principle_metrics,
                    metric_id,
                    file_path,
                )
                if not result.succeeded:
                    return ReviewUnitScoringResult(
                        error_message=(
                            f"{file_path}, unit {unit.name}: metric variable missing "
                            f"during {metric_id} evaluation. Ensure all required fields "
                            "are present per the <submission-metrics-example>. "
                            f"({result.error_message})"
                        )
                    )
                if result.severity is not ReviewSeverity.COMPLIANT:
                    violations.append(
                        ReviewViolation(
                            rule_id=result.metric_id,
                            severity=result.severity,
                        )
                    )

        return ReviewUnitScoringResult(
            unit=replace(unit, violations=tuple(violations))
        )
