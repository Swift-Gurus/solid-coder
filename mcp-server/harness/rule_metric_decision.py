"""Defines one deterministic metric decision in a rule review result."""

from findings.metric_additional_info import MetricAdditionalInfo
from findings.review_severity import ReviewSeverity
from harness.collection_metric_derivation_projection import (
    CollectionMetricDerivationProjection,
)
from harness.metric_scoring_band import MetricComparisonValue, MetricScoringBand
from pydantic import BaseModel, ConfigDict, Field

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
    derivation: CollectionMetricDerivationProjection | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    raw_severity: ReviewSeverity | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
    matching_band: MetricScoringBand | None = Field(
        default=None,
        exclude_if=lambda value: value is None,
    )
