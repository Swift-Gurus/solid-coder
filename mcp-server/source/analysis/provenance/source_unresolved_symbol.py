"""Preserves missing or ambiguous semantic evidence."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceUnresolvedSymbol
solid-category: model
solid-spec: [SPEC-064]
solid-description: Records why a symbol could not be resolved without inferring external ownership from missing evidence.
"""
class SourceUnresolvedSymbol(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["unresolved", "ambiguous"] = "unresolved"
    reason: str = Field(min_length=1)
