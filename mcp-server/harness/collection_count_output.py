"""Defines the output of deterministic intermediate collection counting."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: CollectionCountOutput
solid-category: model
solid-spec: [SPEC-057]
solid-description: Publishes an engine-derived collection size for downstream workflow composition.
"""
class CollectionCountOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    value: int = Field(ge=0)
