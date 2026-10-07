"""Preserves the caller-visible shape of a declared parameter."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceParameterSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records an external parameter label and ordered type syntax without implementation-local names or default expressions.
"""
class SourceParameterSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    external_label: str = Field(min_length=1)
    type_tokens: list[str] = Field(min_length=1)
