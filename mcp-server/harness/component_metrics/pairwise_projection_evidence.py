"""Stores both projected sets for one retained collection item."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from harness.metric_scoring_band import MetricComparisonValue


"""
solid-name: PairwiseProjectionEvidence
solid-category: model
solid-spec: [SPEC-059]
solid-description: Associates original collection indexes with the scalar sets used in pairwise comparisons.
"""
class PairwiseProjectionEvidence(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    index: int
    left: list[Optional[MetricComparisonValue]]
    right: list[Optional[MetricComparisonValue]]
