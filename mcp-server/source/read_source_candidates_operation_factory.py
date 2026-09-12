"""Composes verified candidate-source loading."""

from harness.project_context import ProjectDirectoryReading
from harness.sha256_content_hasher import Sha256ContentHasher
from source.path_source_bytes_reader import PathSourceBytesReader
from source.proposed_candidate_source_resolver import (
    ProposedCandidateSourceResolver,
)
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
    def __init__(self, project_directory: ProjectDirectoryReading) -> None:
        self._project_directory = project_directory

    def make(self) -> ReadSourceCandidatesOperation:
        return ReadSourceCandidatesOperation(
            repository_source=VerifiedCandidateSourceResolver(
                source_bytes=PathSourceBytesReader(),
                content_hasher=Sha256ContentHasher(),
            ),
            proposed_source=ProposedCandidateSourceResolver(),
            project_directory=self._project_directory,
        )
