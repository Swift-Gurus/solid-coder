"""Defines one deterministic top-level source unit."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind
from source.source_line_range import SourceLineRange


"""
solid-name: SourceUnit
solid-category: model
solid-spec: [SPEC-040]
solid-description: Records a stable top-level declaration identity, kind, name, and inclusive source span.
"""
class SourceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    kind: ReviewUnitKind
    name: str = Field(min_length=1)
    span: SourceLineRange
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
