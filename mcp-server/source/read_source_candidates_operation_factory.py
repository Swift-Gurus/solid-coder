"""Composes verified candidate-source loading."""

from harness.sha256_content_hasher import Sha256ContentHasher
from source.path_source_bytes_reader import PathSourceBytesReader
from source.read_source_candidates_operation import ReadSourceCandidatesOperation
from source.verified_candidate_source_resolver import (
    VerifiedCandidateSourceResolver,
)


"""
solid-name: ReadSourceCandidatesOperationFactory
solid-category: factory
solid-spec: [SPEC-040]
solid-description: Creates verified, bounded candidate-source loading operations for deterministic review workflows.
"""
class ReadSourceCandidatesOperationFactory:
    def make(self) -> ReadSourceCandidatesOperation:
        return ReadSourceCandidatesOperation(
            candidate_source=VerifiedCandidateSourceResolver(
                source_bytes=PathSourceBytesReader(),
                content_hasher=Sha256ContentHasher(),
            )
        )
