"""Defines one deterministic metric decision in a rule review result."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from findings.metric_additional_info import MetricAdditionalInfo
from findings.review_severity import ReviewSeverity
from harness.collection_metric_derivation_projection import (
    CollectionMetricDerivationProjection,
)
from harness.metric_scoring_band import MetricComparisonValue, MetricScoringBand


"""
solid-name: RuleMetricDecision
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents one validated metric observation and its MCP-authoritative severity decision.
"""
class RuleMetricDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    metric_id: str
    observation_id: str = "value"
    value: MetricComparisonValue
    severity: ReviewSeverity
    additional_info: MetricAdditionalInfo
    derivation: Optional[CollectionMetricDerivationProjection] = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    raw_severity: Optional[ReviewSeverity] = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    matching_band: Optional[MetricScoringBand] = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
