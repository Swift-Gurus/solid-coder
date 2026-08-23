"""Defines one LLM-selected source candidate identity."""

from typing import Annotated

from pydantic import BaseModel, ConfigDict, StringConstraints


NonEmptyText = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


"""
solid-name: SourceCandidateSelection
solid-category: model
solid-spec: [SPEC-039, SPEC-040]
solid-description: Represents a selected source candidate identity with its selection rationale.
"""
class SourceCandidateSelection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    source_identity: NonEmptyText
    unit_identity: NonEmptyText
    reasoning: NonEmptyText
