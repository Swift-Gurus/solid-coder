"""Loads ordered typed source-search candidates."""

from source.candidate_source_resolving import CandidateSourceResolving
from source.read_source_candidates_input import ReadSourceCandidatesInput
from source.read_source_candidates_output import ReadSourceCandidatesOutput


"""
solid-name: ReadSourceCandidatesOperation
solid-category: service
solid-spec: [SPEC-040]
solid-description: Preserves candidate order while resolving each requested source into a typed read outcome.
"""
class ReadSourceCandidatesOperation:
    def __init__(self, candidate_source: CandidateSourceResolving) -> None:
        self._candidate_source = candidate_source

    def execute(
        self,
        operation_input: ReadSourceCandidatesInput,
    ) -> ReadSourceCandidatesOutput:
        root = operation_input.project_root.resolve()
        return ReadSourceCandidatesOutput(results=[
            self._candidate_source.resolve(
                root,
                candidate,
                operation_input.max_bytes_per_candidate,
            )
            for candidate in operation_input.candidates
        ])
