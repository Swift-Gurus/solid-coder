"""Resolves one candidate against its search-time source identity."""

from pathlib import Path

from harness.content_hashing import ContentHashing
from source.candidate_source_read_kind import CandidateSourceReadKind
from source.candidate_source_resolving import CandidateSourceResolving
from source.loaded_candidate_source import LoadedCandidateSource
from source.read_source_candidates_output import CandidateSourceReadResult
from source.source_bytes_reading import SourceBytesReading
from source.source_search_candidate import SourceSearchCandidate
from source.unavailable_candidate_source import UnavailableCandidateSource


"""
solid-name: VerifiedCandidateSourceResolver
solid-category: service
solid-spec: [SPEC-040]
solid-description: Resolves root-confined candidate bytes, verifies their search-time hash, and bounds returned content.
"""
class VerifiedCandidateSourceResolver(CandidateSourceResolving):
    def __init__(
        self,
        source_bytes: SourceBytesReading,
        content_hasher: ContentHashing,
    ) -> None:
        self._source_bytes = source_bytes
        self._content_hasher = content_hasher

    def resolve(
        self,
        project_root: Path,
        candidate: SourceSearchCandidate,
        maximum_bytes: int,
    ) -> CandidateSourceReadResult:
        path = (project_root / candidate.source_identity).resolve()
        try:
            path.relative_to(project_root)
        except ValueError:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.ESCAPED_ROOT,
                candidate=candidate,
                detail="candidate resolves outside the canonical project root",
            )
        try:
            content_bytes = self._source_bytes.read(path)
        except FileNotFoundError:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.MISSING,
                candidate=candidate,
                detail="candidate no longer exists",
            )
        except OSError as error:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.UNREADABLE,
                candidate=candidate,
                detail=str(error),
            )
        if self._content_hasher.hash(content_bytes) != candidate.content_sha256:
            return UnavailableCandidateSource(
                kind=CandidateSourceReadKind.CHANGED,
                candidate=candidate,
                detail="candidate content changed after repository search",
            )
        bounded = content_bytes[:maximum_bytes]
        return LoadedCandidateSource(
            candidate=candidate,
            content=bounded.decode("utf-8", errors="replace"),
            original_bytes=len(content_bytes),
            truncated=len(content_bytes) > maximum_bytes,
        )
