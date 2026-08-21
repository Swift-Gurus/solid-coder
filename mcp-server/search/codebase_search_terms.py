"""Defines resolved terms for a codebase source search."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: CodebaseSearchTerms
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries normalized source terms and specification identifiers for repository search.
"""
class CodebaseSearchTerms(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    terms: list[str] = Field(default_factory=list)
    specifications: list[str] = Field(default_factory=list)
