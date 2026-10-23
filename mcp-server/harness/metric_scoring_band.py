"""Defines one deterministic severity comparison authored by a metric step."""

from harness.scoring_comparison_operator import ScoringComparisonOperator
from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
)

MetricComparisonValue = StrictBool | StrictInt | StrictFloat | StrictStr


"""
solid-name: MetricScoringBand
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents one typed comparison that maps a validated metric value to a severity.
"""


class MetricScoringBand(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operator: ScoringComparisonOperator
    value: MetricComparisonValue
