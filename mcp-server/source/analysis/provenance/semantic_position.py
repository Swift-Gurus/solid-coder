"""Represents a negotiated UTF-16 language-server document position."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SemanticPosition
solid-category: model
solid-spec: [SPEC-064]
solid-description: Carries a zero-based document line and UTF-16 character coordinate at the semantic protocol boundary.
"""
class SemanticPosition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    line: int = Field(ge=0)
    character: int = Field(ge=0)
