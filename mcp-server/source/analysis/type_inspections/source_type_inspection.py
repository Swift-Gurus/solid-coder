"""Auditable source-local type-inspection facts."""

from pydantic import BaseModel, ConfigDict, Field

from source.analysis.type_inspections.source_type_inspection_kind import SourceTypeInspectionKind
from source.source_byte_range import SourceByteRange
from source.source_line_range import SourceLineRange


"""
solid-name: SourceTypeInspection
solid-category: model
solid-spec: [SPEC-063]
solid-description: Provides an auditable record of a source-local type inspection for deterministic analysis and review.
"""
class SourceTypeInspection(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    kind: SourceTypeInspectionKind
    expression: str = Field(min_length=1)
    operand: str | None = Field(min_length=1)
    target_tokens: list[str]
    span: SourceLineRange
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    operand_range: SourceByteRange | None = None
    destination_range: SourceByteRange | None = None
