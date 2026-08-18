"""Defines the audited exception classification for one rule result."""

from pydantic import BaseModel, ConfigDict

from findings.metric_additional_info import MetricAdditionalInfo


"""
solid-name: RuleExceptionDecision
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents the validated exception flag, reasoning, and source evidence for one rule evaluation.
"""
class RuleExceptionDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    is_exception: bool
    additional_info: MetricAdditionalInfo
