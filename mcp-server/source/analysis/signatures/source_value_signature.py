"""Describes an explicitly typed property declaration."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceValueSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records a property's declared type, available accessor syntax, and modifiers without inferring its implementation behavior.
"""
class SourceValueSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["value"] = "value"
    value_type: list[str] = Field(min_length=1)
    accessors: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
