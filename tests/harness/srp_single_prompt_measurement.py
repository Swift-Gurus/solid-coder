"""Defines one audited scalar returned by the single-prompt SRP experiment."""

from pydantic import BaseModel, ConfigDict, Field

from findings.metric_additional_info import MetricAdditionalInfo


"""
solid-name: SRPSinglePromptMeasurement
solid-category: test-support
solid-spec: [SPEC-036]
solid-description: Maps one schema-validated SRP scalar and its audit evidence from a single model response.
"""
class SRPSinglePromptMeasurement(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: int = Field(ge=0)
    additional_info: MetricAdditionalInfo
