"""Defines a successfully loaded candidate source."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from source.candidate_source_read_kind import CandidateSourceReadKind
from source.source_search_candidate import SourceSearchCandidate

if TYPE_CHECKING:
    from source.analysis.operations.candidate_source_analysis_visitor import CandidateSourceVisitor

VisitResult = TypeVar("VisitResult")


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

    def accept(self, visitor: CandidateSourceVisitor[VisitResult]) -> VisitResult:
        return visitor.visit_loaded(self)
