"""Defines the deterministic aggregate result of a review workflow."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_severity import ReviewSeverity
from harness.rule_review_result import RuleReviewResult


"""
solid-name: ReviewResult
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents the ordered aggregate severity and identified rule results produced by one review workflow run.
"""
class ReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str
    severity: ReviewSeverity
    rule_results: list[RuleReviewResult] = Field(min_length=1)
