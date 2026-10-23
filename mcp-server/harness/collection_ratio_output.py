"""Defines deterministic collection ratio output."""

from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: CollectionRatioOutput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Reports a ratio with auditable numerator, denominator, and empty-value usage.
"""


class CollectionRatioOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: float = Field(ge=0, le=1)
    numerator_count: int = Field(ge=0)
    denominator_count: int = Field(ge=0)
    used_empty_value: bool
