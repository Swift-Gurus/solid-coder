"""Defines resolution of one snapshotted source-search candidate."""

from pathlib import Path
from typing import Protocol

from source.read_source_candidates_output import CandidateSourceReadResult
from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: CandidateSourceResolving
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for resolving one root-confined candidate into bounded content or a typed unavailable outcome.
"""
class CandidateSourceResolving(Protocol):
    def resolve(
        self,
        project_root: Path,
        candidate: SourceSearchCandidate,
        maximum_bytes: int,
    ) -> CandidateSourceReadResult: ...
