"""Projects validated selected identities to discovered candidates."""

from source.validate_candidate_selection_input import ValidateCandidateSelectionInput
from source.validate_candidate_selection_output import ValidateCandidateSelectionOutput


"""
solid-name: ValidateCandidateSelectionOperation
solid-category: service
solid-spec: [SPEC-039, SPEC-040]
solid-description: Resolves validated selected identities to discovered source candidates.
"""
class ValidateCandidateSelectionOperation:
    def execute(
        self,
        operation_input: ValidateCandidateSelectionInput,
    ) -> ValidateCandidateSelectionOutput:
        return ValidateCandidateSelectionOutput(
            selected_candidates=[
                candidate
                for selection in operation_input.selections
                for candidate in operation_input.candidates
                if candidate.source_identity == selection.source_identity
                and candidate.unit_identity == selection.unit_identity
            ],
        )
