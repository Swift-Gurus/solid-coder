"""Defines client overrides for one scored workflow measurement."""

from pydantic import BaseModel, ConfigDict, Field

from harness.review_policy_band_override import ReviewPolicyBandOverride


"""
solid-name: ReviewPolicyMeasurementOverride
solid-category: model
solid-spec: [SPEC-039]
solid-description: Associates a declared measurement name with its requested scoring-band overrides.
"""
class ReviewPolicyMeasurementOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str
    bands: list[ReviewPolicyBandOverride] = Field(default_factory=list)
