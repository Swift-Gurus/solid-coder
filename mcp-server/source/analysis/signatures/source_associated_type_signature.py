"""Preserves an associated type's declared restrictions."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: SourceAssociatedTypeSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Records associated-type bounds, defaults, and constraints without assuming a concrete type substitution.
"""


class SourceAssociatedTypeSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["associated_type"] = "associated_type"
    bounds: list[str] = Field(default_factory=list)
    default_type: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
