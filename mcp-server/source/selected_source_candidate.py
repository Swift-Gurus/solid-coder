"""Defines one validated source candidate selected for inspection."""

from pydantic import BaseModel, ConfigDict

from source.source_candidate_disposition import CandidateId
from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: SelectedSourceCandidate
solid-category: model
solid-spec: [SPEC-056]
solid-description: Associates one stable presented candidate ID with its server-owned source-search record.
"""
class SelectedSourceCandidate(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: CandidateId
    source: SourceSearchCandidate
