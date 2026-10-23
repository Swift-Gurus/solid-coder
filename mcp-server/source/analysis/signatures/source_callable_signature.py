"""Describes a callable declaration without its implementation body."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field
from source.analysis.signatures.source_parameter_signature import (
    SourceParameterSignature,
)

"""
solid-name: SourceCallableSignature
solid-category: model
solid-spec: [SPEC-057]
solid-description: Preserves ordered callable parameters, result syntax, modifiers, and generic constraints for structural analysis without asserting semantic equivalence.
"""


class SourceCallableSignature(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["callable"] = "callable"
    parameters: list[SourceParameterSignature] = Field(default_factory=list)
    return_type: list[str] = Field(default_factory=list)
    modifiers: list[str] = Field(default_factory=list)
    generic_parameters: list[str] = Field(default_factory=list)
    constraints: list[str] = Field(default_factory=list)
