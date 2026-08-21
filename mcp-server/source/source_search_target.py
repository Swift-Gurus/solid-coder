"""Defines one immutable MCP-owned source-search target."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind
from source.source_line_range import SourceLineRange
from source.source_search_query import SearchTerm


"""
solid-name: SourceSearchTarget
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries stable source identity, exact reviewed code, and deterministic terms for one semantic search task.
"""
class SourceSearchTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    source_identity: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: ReviewUnitKind
    span: SourceLineRange
    code: str
    deterministic_terms: list[SearchTerm] = Field(min_length=1)
