"""Defines client overrides for one engine-scored workflow metric."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.review_policy_measurement_override import ReviewPolicyMeasurementOverride


"""
solid-name: ReviewPolicyMetricOverride
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries optional metric enablement and typed measurement scoring overrides.
"""
class ReviewPolicyMetricOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    enabled: Optional[bool] = None
    reason: Optional[str] = None
    measurements: list[ReviewPolicyMeasurementOverride] = Field(default_factory=list)
