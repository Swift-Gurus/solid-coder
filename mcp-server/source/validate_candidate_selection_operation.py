"""Projects validated dispositions to inspected candidates and audit records."""

from source.source_candidate_disposition_kind import (
    SourceCandidateDispositionKind,
)
from source.selected_source_candidate import SelectedSourceCandidate
from source.validate_candidate_selection_input import ValidateCandidateSelectionInput
from source.validate_candidate_selection_output import ValidateCandidateSelectionOutput
from validation.collection_identity_coverage_validator import CollectionIdentityCoverageValidating


"""
solid-name: ValidateCandidateSelectionOperation
solid-category: service
solid-spec: [SPEC-039, SPEC-040, SPEC-056]
solid-description: Resolves complete candidate dispositions into source-ordered inspection work and audit records.
"""
class ValidateCandidateSelectionOperation:
    def __init__(self, coverage_validator: CollectionIdentityCoverageValidating) -> None:
        self._coverage_validator = coverage_validator

    def execute(
        self,
        operation_input: ValidateCandidateSelectionInput,
    ) -> ValidateCandidateSelectionOutput:
        self._coverage_validator.validate(
            expected_ids=[f"candidate-{index}" for index in range(1, len(operation_input.candidates) + 1)],
            submitted_ids=[item.candidate_id for item in operation_input.dispositions],
            identity_name="candidate",
        )
        ordered_dispositions = [
            next(
                disposition
                for disposition in operation_input.dispositions
                if disposition.candidate_id == f"candidate-{index}"
            )
            for index in range(1, len(operation_input.candidates) + 1)
        ]
        return ValidateCandidateSelectionOutput(
            selected_candidates=[
                SelectedSourceCandidate(
                    candidate_id=disposition.candidate_id,
                    source=candidate,
                )
                for candidate, disposition in zip(
                    operation_input.candidates,
                    ordered_dispositions,
                )
                if disposition.disposition
                is SourceCandidateDispositionKind.INSPECT
            ],
            dispositions=ordered_dispositions,
        )
