"""Defines auditable source provenance for one finalized rule execution."""

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: RuleReviewProvenance
solid-category: model
solid-spec: [SPEC-039, SPEC-041]
solid-description: Identifies the workflow scope and ordered review source that produced one rule decision.
"""
class RuleReviewProvenance(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    kind: Literal["root", "included"]
    scope_identity: str = Field(min_length=1)
    source_index: int = Field(ge=0)
