"""Defines the normalized deterministic result of one executable review rule."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from findings.review_severity import ReviewSeverity
from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_decision import RuleMetricDecision
from harness.rule_review_provenance import RuleReviewProvenance


"""
solid-name: RuleReviewResult
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents one identified finalized rule execution with metric decisions, severity, and audited exception classification.
"""
class RuleReviewResult(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str
    rule_instance_id: str
    provenance: RuleReviewProvenance
    severity: ReviewSeverity
    scoring_authority: Literal["mcp"] = "mcp"
    exception: RuleExceptionDecision
    metrics: list[RuleMetricDecision] = Field(min_length=1)
