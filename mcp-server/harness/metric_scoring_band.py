"""Defines one deterministic severity comparison authored by a metric step."""

from typing import Union

from pydantic import (
    BaseModel,
    ConfigDict,
    StrictBool,
    StrictFloat,
    StrictInt,
    StrictStr,
)

from harness.scoring_comparison_operator import ScoringComparisonOperator


MetricComparisonValue = Union[StrictBool, StrictInt, StrictFloat, StrictStr]


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
