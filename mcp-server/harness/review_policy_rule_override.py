"""Defines client overrides for one executable review-rule workflow."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.review_policy_metric_override import ReviewPolicyMetricOverride
from harness.workflow_id import WorkflowId


"""
solid-name: ReviewPolicyRuleOverride
solid-category: model
solid-spec: [SPEC-039]
solid-description: Associates a workflow ID with optional enablement and engine-scoring overrides.
"""
class ReviewPolicyRuleOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: WorkflowId
    enabled: Optional[bool] = None
    reason: Optional[str] = None
    metrics: list[ReviewPolicyMetricOverride] = Field(default_factory=list)
