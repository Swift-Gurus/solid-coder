"""Defines validated observations collected from one executable review rule."""

from pydantic import BaseModel, ConfigDict, Field

from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_metric_observation import RuleMetricObservation


"""
solid-name: RuleObservations
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents the complete validated observations required to finalize one review rule.
"""
class RuleObservations(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metrics: list[RuleMetricObservation] = Field(min_length=1)
    exception: RuleExceptionDecision
