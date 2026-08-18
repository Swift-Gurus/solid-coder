"""Defines one validated metric observation awaiting deterministic scoring."""

from pydantic import BaseModel, ConfigDict

from findings.metric_additional_info import MetricAdditionalInfo
from harness.metric_declaration import MetricDeclaration
from harness.metric_scoring_band import MetricComparisonValue


"""
solid-name: RuleMetricObservation
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents a validated metric observation for deterministic scoring.
"""
class RuleMetricObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration: MetricDeclaration
    value: MetricComparisonValue
    additional_info: MetricAdditionalInfo
