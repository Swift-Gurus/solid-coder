"""Defines one expected metric result for live rule validation."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_severity import ReviewSeverity
from harness.metric_scoring_band import MetricComparisonValue


"""
solid-name: RuleMetricResultExpectation
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries one expected metric identity, scalar observation, and server severity from a live rule scenario.
"""
class RuleMetricResultExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    observation_id: str = Field(default="value", min_length=1)
    value: MetricComparisonValue
    severity: ReviewSeverity
