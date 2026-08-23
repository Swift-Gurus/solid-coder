"""Defines typed input for repository source search."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field, StringConstraints

from source.source_search_query import SourceSearchQuery
from source.source_unit_identity import SourceUnitIdentity
from source.source_search_context import SourceSearchContext


SourceFileExtension = Annotated[
    str,
    StringConstraints(
        pattern=r"^\.[a-z0-9][a-z0-9+_-]*$",
    ),
]


"""
solid-name: SourceSearchInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Defines a validated source-search request for deterministic repository comparison.
"""
class SourceSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    queries: Annotated[list[SourceSearchQuery], Field(min_length=1)]
    excluded_units: list[SourceUnitIdentity] = Field(default_factory=list)
    context: SourceSearchContext = Field(default_factory=SourceSearchContext)
    included_file_extensions: list[SourceFileExtension] = Field(
        default_factory=list,
    )
    max_candidates: int = Field(default=20, ge=1, le=100)
