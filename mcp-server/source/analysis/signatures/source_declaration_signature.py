"""Typed declaration header facts for later structural relationship resolution."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.signatures.source_type_reference import SourceTypeReference

"""
solid-name: SourceDeclarationSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Carries an authored declaration name, inherited references, generic parameters, constraints, and modifiers without asserting semantic conformance.
"""


class SourceDeclarationSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["declaration"] = "declaration"
    name: SourceTypeReference
    inherited_types: list[SourceTypeReference] = Field(default_factory=list)
    generic_parameters: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
