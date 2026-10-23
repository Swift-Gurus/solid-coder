"""Defines typed input for complete source-candidate disposition validation."""

from pydantic import BaseModel, ConfigDict
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
