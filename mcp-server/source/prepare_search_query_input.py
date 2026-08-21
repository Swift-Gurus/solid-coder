"""Defines deterministic source-search query preparation input."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from source.source_search_query import SearchTerm
from source.source_search_target import SourceSearchTarget


"""
solid-name: PrepareSearchQueryInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Defines validated inputs for deterministic source-search query preparation.
"""
class PrepareSearchQueryInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: SourceSearchTarget
    generated_terms: Annotated[list[SearchTerm], Field(min_length=1)]
    excluded_source_identities: list[str] = Field(default_factory=list)
