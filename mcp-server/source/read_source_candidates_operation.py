"""Loads ordered typed source-search candidates."""

from harness.project_context import ProjectDirectoryReading
from source.candidate_source_resolving import CandidateSourceResolving
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_output import ReadSourceCandidatesOutput
from source.repository_target_resolver import RepositoryTargetResolving
from source.source_candidate_origin import SourceCandidateOrigin

"""
solid-name: ReadSourceCandidatesOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Preserves candidate order while resolving each requested source into a typed read outcome.
"""


class ReadSourceCandidatesOperation:
    def __init__(
        self,
        repository_source: CandidateSourceResolving,
        proposed_source: CandidateSourceResolving,
        project_directory: ProjectDirectoryReading,
        targets: RepositoryTargetResolving,
    ) -> None:
        self._repository_source = repository_source
        self._proposed_source = proposed_source
        self._project_directory = project_directory
        self._targets = targets

    def execute(
        self,
        operation_input: ReadSourceCandidatesInput,
    ) -> ReadSourceCandidatesOutput:
        cwd = self._project_directory.read()
        root = self._targets.resolve(cwd, cwd.resolve())
        for candidate in operation_input.candidates:
            self._targets.resolve(root, candidate.path)
            self._targets.resolve(root, root / candidate.source_identity)
        for source in operation_input.context.sources:
            self._targets.resolve(root, source.path)
        return ReadSourceCandidatesOutput(
            results=[
                (
                    self._proposed_source
                    if candidate.origin is SourceCandidateOrigin.PROPOSED
                    else self._repository_source
                ).resolve(
                    root,
                    candidate,
                    operation_input.max_bytes_per_candidate,
                    operation_input.context,
                )
                for candidate in operation_input.candidates
            ]
        )
