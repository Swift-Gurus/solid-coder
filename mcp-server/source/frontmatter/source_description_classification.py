"""One evidenced semantic judgment about an authored description."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from findings.metric_additional_info import MetricAdditionalInfo


"""
solid-name: SourceDescriptionClassification
solid-category: model
solid-spec: [SPEC-069]
solid-description: Carries an identity-bound description classification and its supporting reasoning and evidence.
"""
class SourceDescriptionClassification(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    declaration_id: str = Field(min_length=1)
    classification: Literal["CAPABILITY", "IMPLEMENTATION_DETAIL", "VAGUE", "INVALID_FORMAT"]
    additional_info: MetricAdditionalInfo
