"""Defines aggregate severity selection for deterministic review decisions."""

from typing import Protocol

from findings.review_severity import ReviewSeverity
from harness.rule_metric_decision import RuleMetricDecision


"""
solid-name: ReviewSeveritySelecting
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for selecting aggregate review severity from metric decisions.
"""
class ReviewSeveritySelecting(Protocol):
    def select(
        self,
        decisions: list[RuleMetricDecision],
    ) -> ReviewSeverity: ...
