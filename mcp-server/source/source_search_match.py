"""Defines typed provenance for one repository search match."""

from pydantic import BaseModel, ConfigDict

from source.source_search_match_kind import SourceSearchMatchKind


"""
solid-name: SourceSearchMatch
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries the query identity, exact term, and source fact for one candidate match.
"""
class SourceSearchMatch(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    query_id: str
    term: str
    kind: SourceSearchMatchKind
