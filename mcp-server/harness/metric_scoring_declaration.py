"""Defines the severity bands authored by one metric step."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, model_validator

from harness.metric_scoring_band import MetricScoringBand


"""
solid-name: MetricScoringDeclaration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Holds the optional minor and severe deterministic scoring bands for one metric.
"""
class MetricScoringDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    minor: Optional[MetricScoringBand] = None
    severe: Optional[MetricScoringBand] = None

    @model_validator(mode="after")
    def require_a_band(self) -> "MetricScoringDeclaration":
        if self.minor is None and self.severe is None:
            raise ValueError("metric scoring must declare at least one severity band")
        return self
