"""Defines a successfully loaded candidate source."""

from typing import Literal

from pydantic import BaseModel, ConfigDict

from source.candidate_source_read_kind import CandidateSourceReadKind
from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: LoadedCandidateSource
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries the exact bounded candidate content used by downstream comparison and replay.
"""
class LoadedCandidateSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal[CandidateSourceReadKind.LOADED] = CandidateSourceReadKind.LOADED
    candidate: SourceSearchCandidate
    content: str
    original_bytes: int
    truncated: bool
