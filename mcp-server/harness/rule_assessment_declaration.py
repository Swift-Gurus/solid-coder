"""Defines all observations collected by one aggregate rule step."""

from pydantic import BaseModel, ConfigDict, Field, model_validator

from harness.metric_declaration import MetricDeclaration, MetricObservationId
from harness.rule_assessment_supporting_output import (
    RuleAssessmentSupportingOutput,
)


"""
solid-name: RuleAssessmentDeclaration
solid-category: model
solid-spec: [SPEC-044]
solid-description: Declares the metric and exception observations collected together by one agent-owned rule assessment.
"""
class RuleAssessmentDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    supporting_outputs: list[RuleAssessmentSupportingOutput] = Field(
        default_factory=list,
    )
    metrics: list[MetricDeclaration] = Field(min_length=1)
    exception_observation_id: MetricObservationId = "exception"

    @model_validator(mode="after")
    def validate_observation_ids(self) -> "RuleAssessmentDeclaration":
        metric_ids = [metric.observation_id for metric in self.metrics]
        if len(metric_ids) != len(set(metric_ids)):
            raise ValueError(
                "aggregate metric observation IDs must be unique"
            )
        if self.exception_observation_id in metric_ids:
            raise ValueError(
                "exception observation ID must differ from metric observation IDs"
            )
        supporting_names = [output.name for output in self.supporting_outputs]
        if len(supporting_names) != len(set(supporting_names)):
            raise ValueError("aggregate supporting output names must be unique")
        reserved_names = [*metric_ids, self.exception_observation_id]
        if any(name in reserved_names for name in supporting_names):
            raise ValueError(
                "aggregate supporting output names must differ from observation IDs"
            )
        return self
