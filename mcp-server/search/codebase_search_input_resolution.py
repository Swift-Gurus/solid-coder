"""Defines resolved typed input for a codebase source search."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_search_input import SourceSearchInput


"""
solid-name: CodebaseSearchInputResolution
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries validated source-search input and its minimum-match threshold.
"""
class CodebaseSearchInputResolution(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    operation_input: SourceSearchInput
    minimum_matches: int = Field(ge=1)
