"""Defines typed input for bounded candidate-source loading."""

from pydantic import BaseModel, ConfigDict, Field

from source.source_search_candidate import SourceSearchCandidate
from source.source_search_context import SourceSearchContext


"""
solid-name: ReadSourceCandidatesInput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Selects typed search candidates and the per-candidate content bound used for audit and replay.
"""
class ReadSourceCandidatesInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: list[SourceSearchCandidate]
    context: SourceSearchContext = Field(default_factory=SourceSearchContext)
    max_bytes_per_candidate: int = Field(default=65_536, ge=1, le=1_048_576)
