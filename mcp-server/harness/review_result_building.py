"""Defines deterministic construction of an aggregate review result."""

from typing import Protocol

from harness.review_result import ReviewResult
from harness.rule_review_result import RuleReviewResult


"""
solid-name: ReviewResultBuilding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for building one aggregate review result from ordered finalized rule results.
"""
class ReviewResultBuilding(Protocol):
    def build(
        self,
        workflow_id: str,
        rule_results: list[RuleReviewResult],
    ) -> ReviewResult: ...
