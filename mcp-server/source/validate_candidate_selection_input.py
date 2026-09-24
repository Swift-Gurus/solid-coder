"""Defines typed input for complete source-candidate disposition validation."""

from pydantic import BaseModel, ConfigDict, model_validator

from source.source_candidate_disposition import SourceCandidateDisposition
from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: ValidateCandidateSelectionInput
solid-category: model
solid-spec: [SPEC-039, SPEC-040, SPEC-056]
solid-description: Carries discovered candidates and the complete model disposition set for validation.
"""
class ValidateCandidateSelectionInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidates: list[SourceSearchCandidate]
    dispositions: list[SourceCandidateDisposition]

    @model_validator(mode="after")
    def validate_complete_coverage(self) -> "ValidateCandidateSelectionInput":
        expected_ids = [
            f"candidate-{index}"
            for index in range(1, len(self.candidates) + 1)
        ]
        submitted_ids = [
            disposition.candidate_id
            for disposition in self.dispositions
        ]
        duplicate_ids = [
            candidate_id
            for index, candidate_id in enumerate(submitted_ids)
            if candidate_id in submitted_ids[:index]
            and candidate_id not in submitted_ids[index + 1:]
        ]
        missing_ids = [
            candidate_id
            for candidate_id in expected_ids
            if candidate_id not in submitted_ids
        ]
        unknown_ids = [
            candidate_id
            for candidate_id in submitted_ids
            if candidate_id not in expected_ids
        ]
        problems = []
        if missing_ids:
            problems.append(f"missing candidate IDs {missing_ids}")
        if duplicate_ids:
            problems.append(f"duplicate candidate IDs {duplicate_ids}")
        if unknown_ids:
            problems.append(f"unknown candidate IDs {unknown_ids}")
        if problems:
            raise ValueError(
                "Candidate disposition submission is incomplete: "
                + "; ".join(problems)
                + ". Resubmit one complete replacement disposition for every "
                "presented candidate ID."
            )
        return self
