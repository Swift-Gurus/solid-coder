"""Defines one complete disposition for a presented source candidate."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints

from source.source_candidate_disposition_kind import (
    SourceCandidateDispositionKind,
)


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]
CandidateId = Annotated[
    str,
    StringConstraints(pattern=r"^candidate-[1-9][0-9]*$"),
]


"""
solid-name: SourceCandidateDisposition
solid-category: model
solid-spec: [SPEC-056]
solid-description: Carries an audited inspect-or-reject decision for one server-identified search candidate.
"""
class SourceCandidateDisposition(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: CandidateId
    disposition: SourceCandidateDispositionKind
    reasoning: NonEmptyText
    evidence: NonEmptyText
