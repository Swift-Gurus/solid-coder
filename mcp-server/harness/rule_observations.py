"""Defines validated observations collected from one executable review rule."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_observation import RuleMetricObservation
from harness.unavailable_rule_metric import UnavailableRuleMetric


"""
solid-name: RuleObservations
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents the complete validated observations required to finalize one review rule.
"""
class RuleObservations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metrics: list[RuleMetricObservation]
    unavailable_metrics: list[UnavailableRuleMetric] = Field(default_factory=list)
    exception: RuleExceptionDecision

    @model_validator(mode="after")
    def require_metric_outcomes(self) -> "RuleObservations":
        if not self.metrics and not self.unavailable_metrics:
            raise ValueError("Rule observations require measured or unavailable metrics")
        return self
