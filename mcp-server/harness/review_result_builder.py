"""Builds aggregate review results from finalized rule decisions."""

from harness.review_result import ReviewResult
from harness.review_result_building import ReviewResultBuilding
from harness.review_severity_selecting import ReviewSeveritySelecting
from harness.rule_review_result import RuleReviewResult


"""
solid-name: ReviewResultBuilder
solid-category: service
solid-spec: [SPEC-039]
solid-description: Builds an ordered review aggregate with deterministic worst-severity selection across rule metrics.
"""
class ReviewResultBuilder(ReviewResultBuilding):
    def __init__(self, severity_selector: ReviewSeveritySelecting) -> None:
        self._severity_selector = severity_selector

    def build(
        self,
        workflow_id: str,
        rule_results: list[RuleReviewResult],
    ) -> ReviewResult:
        return ReviewResult(
            workflow_id=workflow_id,
            severity=self._severity_selector.select([
                metric
                for result in rule_results
                for metric in result.metrics
            ]),
            rule_results=rule_results,
        )
