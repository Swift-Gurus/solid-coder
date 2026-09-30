"""Defines the source-search data needed to present candidates."""

from pydantic import BaseModel, ConfigDict

from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: SourceSearchResults
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries typed candidates and the scanned-file count shared by search and presentation.
"""
class SourceSearchResults(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: list[SourceSearchCandidate]
    files_scanned: int
