"""Defines the auditable result of matching one review rule to one unit."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


RuleMatchDimension = Literal[
    "all",
    "file_extensions",
    "unit_kinds",
    "tags",
]


"""
solid-name: RuleApplicabilityDecision
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records whether a rule matched and the decisive matcher evidence.
"""
class RuleApplicabilityDecision(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    applicable: bool
    dimension: RuleMatchDimension
    reason: str = Field(min_length=1)
    decisive_values: list[str] = Field(default_factory=list)
