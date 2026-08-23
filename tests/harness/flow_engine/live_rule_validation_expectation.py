"""Defines exact expected outputs for one live executable-rule scenario."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_severity import ReviewSeverity
from rule_metric_result_expectation import RuleMetricResultExpectation


"""
solid-name: LiveRuleValidationExpectation
solid-category: test-support
solid-spec: [SPEC-039]
solid-description: Carries ordered metric, exception, severity, and auxiliary-step expectations consumed by the shared live rule assertion contract.
"""
class LiveRuleValidationExpectation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_id: str = Field(min_length=1)
    metrics: list[RuleMetricResultExpectation] = Field(min_length=1)
    final_severity: ReviewSeverity
    is_exception: bool = False
    allow_auxiliary_steps: bool = False
