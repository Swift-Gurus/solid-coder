"""Defines one auditable boolean observation used by collection ratios."""

from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: CollectionRatioObservation
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries one included or excluded ratio decision with model-supplied reasoning and evidence.
"""


class CollectionRatioObservation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observation_id: str = Field(min_length=1)
    matches: bool
    included: bool = True
    reasoning: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
