from typing import Protocol

from harness.review_result import ReviewResult
from health_check_outcome import HealthCheckOutcome
from review_violation_selecting import ReviewViolationSelecting
from source.analysis.operations.source_introduction_evidence import (
    SourceIntroductionEvidence,
)
from unavailable_health_metric import UnavailableHealthMetric

"""
solid-name: HealthReviewAssessing
solid-category: abstraction
solid-description: Contract for deciding write-gate outcomes from scored reviews and verified source-introduction evidence.
"""


class HealthReviewAssessing(Protocol):
    def assess(
        self, result: ReviewResult, introductions: SourceIntroductionEvidence
    ) -> HealthCheckOutcome: ...


"""
solid-name: HealthReviewAssessor
solid-category: service
solid-spec: [SPEC-057]
solid-description: Preserves measured violations and distinguishes exempt, warning-eligible, and blocking unavailable review outcomes.
"""


class HealthReviewAssessor(HealthReviewAssessing):
    def __init__(self, violations: ReviewViolationSelecting) -> None:
        self._violations = violations

    def assess(
        self, result: ReviewResult, introductions: SourceIntroductionEvidence
    ) -> HealthCheckOutcome:
        return HealthCheckOutcome(
            violations=self._violations.select(result),
            unavailable_metrics=[
                UnavailableHealthMetric(
                    workflow_id=rule.workflow_id,
                    rule_instance_id=rule.rule_instance_id,
                    provenance=rule.provenance,
                    metric=metric,
                    exception=rule.exception,
                    blocks_write=(
                        not rule.exception.is_exception
                        and rule.provenance.source_unit
                        not in introductions.verified_interfaces
                    ),
                )
                for rule in result.rule_results
                for metric in rule.unavailable_metrics
            ],
            introduction_evidence=introductions,
        )
