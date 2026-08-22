"""Defines the stable identity of one source unit."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceUnitIdentity
solid-category: model
solid-spec: [SPEC-040]
solid-description: Identifies one unit independently from its containing source so search can exclude self without excluding sibling units.
"""
class SourceUnitIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_identity: str = Field(min_length=1)
    unit_identity: str = Field(min_length=1)
