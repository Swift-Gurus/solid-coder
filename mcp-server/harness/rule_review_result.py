"""Defines the normalized deterministic result of one executable review rule."""

from typing import Literal

from findings.review_severity import ReviewSeverity
from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_decision import RuleMetricDecision
from harness.rule_review_provenance import RuleReviewProvenance
from harness.unavailable_rule_metric import UnavailableRuleMetric
from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    severity: ReviewSeverity | None
    scoring_authority: Literal["mcp"] = "mcp"
    exception: RuleExceptionDecision
    metrics: list[RuleMetricDecision]
    unavailable_metrics: list[UnavailableRuleMetric] = Field(default_factory=list)

    @model_validator(mode="after")
    def validate_metric_outcomes(self) -> "RuleReviewResult":
        if not self.metrics and not self.unavailable_metrics:
            raise ValueError("A rule result requires measured or unavailable metrics")
        if bool(self.metrics) != (self.severity is not None):
            raise ValueError("A rule severity requires measured metrics")
        return self
