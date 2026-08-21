"""Defines typed input for repository source search."""

from pathlib import Path
from typing import Annotated

from pydantic import BaseModel, ConfigDict, Field

from source.source_search_query import SourceSearchQuery


"""
solid-name: SourceSearchInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Selects one project, typed queries, source exclusions, and a bounded candidate limit.
"""
class SourceSearchInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    project_root: Path
    queries: Annotated[list[SourceSearchQuery], Field(min_length=1)]
    excluded_source_identities: list[str] = Field(default_factory=list)
    max_candidates: int = Field(default=20, ge=1, le=100)
