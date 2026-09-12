"""Selects blocking metrics from an authoritative review result."""

from findings.review_severity import ReviewSeverity
from harness.review_result import ReviewResult
from health_violation import HealthViolation


"""
solid-name: ScoredReviewViolationSelector
solid-category: service
solid-spec: [SPEC-036, SPEC-039]
solid-description: Converts severe scored metric decisions into health violations.
"""
class ScoredReviewViolationSelector:
    def select(self, result: ReviewResult) -> list[HealthViolation]:
        return [
            HealthViolation(
                principle=rule.workflow_id,
                metric_id=metric.metric_id,
                issue=metric.additional_info.reasoning,
                evidence=metric.additional_info.evidence,
            )
            for rule in result.rule_results
            for metric in rule.metrics
            if metric.severity is ReviewSeverity.SEVERE
        ]
