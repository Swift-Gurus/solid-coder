"""Defines auditable reasoning and evidence for one metric measurement."""

from pydantic import ConfigDict, Field
from pydantic.dataclasses import dataclass


"""
solid-name: MetricAdditionalInfo
solid-category: model
solid-description: Carries the required reasoning and source evidence supporting one submitted metric measurement.
"""
@dataclass(frozen=True, config=ConfigDict(extra="forbid"))
class MetricAdditionalInfo:
    reasoning: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
