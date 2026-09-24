"""Defines validated source-candidate disposition output."""

from pydantic import BaseModel, ConfigDict

from source.selected_source_candidate import SelectedSourceCandidate
from source.source_candidate_disposition import SourceCandidateDisposition


"""
solid-name: ValidateCandidateSelectionOutput
solid-category: model
solid-spec: [SPEC-039, SPEC-040, SPEC-056]
solid-description: Returns inspected candidate records and the complete audited disposition set.
"""
class ValidateCandidateSelectionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    selected_candidates: list[SelectedSourceCandidate]
    dispositions: list[SourceCandidateDisposition]
