"""Defines inputs for deterministic collection ratio calculation."""

from pydantic import BaseModel, ConfigDict, Field

from harness.collection_ratio_observation import CollectionRatioObservation


"""
solid-name: CollectionRatioInput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Supplies typed ratio observations and an optional neutral value for an empty denominator.
"""
class CollectionRatioInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    observations: list[CollectionRatioObservation]
    empty_value: float = Field(default=1.0, ge=0, le=1)
