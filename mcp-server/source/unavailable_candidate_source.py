"""Defines a typed failed candidate-source read outcome."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal, TypeVar

from pydantic import BaseModel, ConfigDict

from source.candidate_source_read_kind import CandidateSourceReadKind
from source.source_search_candidate import SourceSearchCandidate

if TYPE_CHECKING:
    from source.analysis.operations.candidate_source_analysis_visitor import CandidateSourceVisitor

VisitResult = TypeVar("VisitResult")

UnavailableCandidateSourceKind = Literal[
    CandidateSourceReadKind.MISSING,
    CandidateSourceReadKind.UNREADABLE,
    CandidateSourceReadKind.ESCAPED_ROOT,
    CandidateSourceReadKind.CHANGED,
]


"""
solid-name: UnavailableCandidateSource
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries a candidate and the auditable reason its snapshotted source could not be loaded.
"""
class UnavailableCandidateSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: UnavailableCandidateSourceKind
    candidate: SourceSearchCandidate
    detail: str

    def accept(self, visitor: CandidateSourceVisitor[VisitResult]) -> VisitResult:
        return visitor.visit_unavailable(self)
