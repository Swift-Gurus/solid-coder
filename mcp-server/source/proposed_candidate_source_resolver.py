"""Resolves bounded candidate content from proposed source snapshots."""

from pathlib import Path

from source.candidate_source_read_kind import CandidateSourceReadKind
from source.loaded_candidate_source import LoadedCandidateSource
from source.read_source_candidates_output import CandidateSourceReadResult
from source.source_search_context import SourceSearchContext
from source.source_search_candidate import SourceSearchCandidate
from source.unavailable_candidate_source import UnavailableCandidateSource


"""
solid-name: ProposedCandidateSourceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves bounded candidate content from authoritative prospective source context.
"""
class ProposedCandidateSourceResolver:
    def resolve(
        self,
        project_root: Path,
        candidate: SourceSearchCandidate,
        maximum_bytes: int,
        context: SourceSearchContext,
    ) -> CandidateSourceReadResult:
        try:
            candidate.path.resolve().relative_to(project_root)
        except ValueError:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.ESCAPED_ROOT,
                candidate=candidate,
                detail="candidate resolves outside the canonical project root",
            )
        snapshot = next(
            (
                source
            for source in context.sources
                if source.path.resolve() == candidate.path.resolve()
            ),
            None,
        )
        if snapshot is None:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.MISSING,
                candidate=candidate,
                detail="proposed candidate context is unavailable",
            )
        if snapshot.content_sha256 != candidate.content_sha256:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.CHANGED,
                candidate=candidate,
                detail="proposed candidate changed after source search",
            )
        content_bytes = snapshot.content.encode("utf-8")
        unit_bytes = content_bytes[
            candidate.start_offset:candidate.end_offset + 1
        ]
        bounded = unit_bytes[:maximum_bytes]
        return LoadedCandidateSource(
            candidate=candidate,
            content=bounded.decode("utf-8", errors="replace"),
            original_bytes=len(unit_bytes),
            truncated=len(unit_bytes) > maximum_bytes,
        )
