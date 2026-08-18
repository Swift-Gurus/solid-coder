"""Selects the worst severity present in deterministic review decisions."""

from findings.review_severity import ReviewSeverity
from harness.review_severity_selecting import ReviewSeveritySelecting
from harness.rule_metric_decision import RuleMetricDecision


"""
solid-name: WorstReviewSeveritySelector
solid-category: service
solid-spec: [SPEC-039]
solid-description: Selects the highest-impact severity from metric decisions.
"""
class WorstReviewSeveritySelector(ReviewSeveritySelecting):
    def select(
        self,
        decisions: list[RuleMetricDecision],
    ) -> ReviewSeverity:
        if any(
            decision.severity is ReviewSeverity.SEVERE
            for decision in decisions
        ):
            return ReviewSeverity.SEVERE
        if any(
            decision.severity is ReviewSeverity.MINOR
            for decision in decisions
        ):
            return ReviewSeverity.MINOR
        return ReviewSeverity.COMPLIANT
