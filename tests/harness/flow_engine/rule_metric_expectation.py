"""Defines one typed metric expectation for deterministic rule-flow tests."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_severity import ReviewSeverity
from harness.metric_scoring_band import MetricComparisonValue


"""
solid-name: RuleMetricExpectation
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries one rule metric's workflow step, canonical detection block, expected observation, and severity.
"""
class RuleMetricExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    step_id: str = Field(min_length=1)
    metric_id: str = Field(min_length=1)
    detection_id: str = Field(min_length=1)
    detection_name: str = Field(min_length=1)
    value: MetricComparisonValue
    severity: ReviewSeverity
