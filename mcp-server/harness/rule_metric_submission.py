"""Defines one audited metric value submitted inside an aggregate assessment."""

from pydantic import BaseModel, ConfigDict

from findings.metric_additional_info import MetricAdditionalInfo
from harness.metric_scoring_band import MetricComparisonValue


"""
solid-name: RuleMetricSubmission
solid-category: model
solid-spec: [SPEC-044]
solid-description: Represents one validated metric value and its audit information within an aggregate rule response.
"""
class RuleMetricSubmission(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: MetricComparisonValue
    additional_info: MetricAdditionalInfo
