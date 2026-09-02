"""Defines typed input for source-candidate selection validation."""

from pydantic import BaseModel, ConfigDict, model_validator

from source.source_candidate_selection import SourceCandidateSelection
from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: ValidateCandidateSelectionInput
solid-category: model
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries discovered candidates and selected identities for validation.
"""
class ValidateCandidateSelectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: list[SourceSearchCandidate]
    selections: list[SourceCandidateSelection]

    @model_validator(mode="after")
    def validate_selected_identities(self) -> "ValidateCandidateSelectionInput":
        for selection_index, selection in enumerate(self.selections):
            if any(
                accepted.path == selection.path
                and accepted.unit == selection.unit
                for accepted in self.selections[:selection_index]
            ):
                raise ValueError(
                    "Candidate selection contains duplicate reference "
                    f"'{selection.path}#{selection.unit}'"
                )
            if not any(
                str(candidate.path) == selection.path
                and candidate.unit == selection.unit
                for candidate in self.candidates
            ):
                raise ValueError(
                    "Candidate selection contains unknown reference "
                    f"'{selection.path}#{selection.unit}'"
                )
        return self
