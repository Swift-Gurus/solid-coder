"""Defines validated source-candidate selection output."""

from pydantic import BaseModel, ConfigDict

from source.source_search_candidate import SourceSearchCandidate


"""
solid-name: ValidateCandidateSelectionOutput
solid-category: model
solid-spec: [SPEC-039, SPEC-040]
solid-description: Returns the discovered candidate records matching validated selected identities.
"""
class ValidateCandidateSelectionOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    selected_candidates: list[SourceSearchCandidate]
