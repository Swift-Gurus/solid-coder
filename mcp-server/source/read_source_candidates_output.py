"""Defines typed output for candidate-source loading."""

from typing import Annotated, Union

from pydantic import BaseModel, ConfigDict, Field

from source.loaded_candidate_source import LoadedCandidateSource
from source.unavailable_candidate_source import UnavailableCandidateSource

CandidateSourceReadResult = Annotated[
    Union[LoadedCandidateSource, UnavailableCandidateSource],
    Field(discriminator="kind"),
]


"""
solid-name: ReadSourceCandidatesOutput
solid-category: model
solid-spec: [SPEC-040]
solid-description: Returns ordered loaded or unavailable outcomes for every requested search candidate.
"""
class ReadSourceCandidatesOutput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    results: list[CandidateSourceReadResult]
