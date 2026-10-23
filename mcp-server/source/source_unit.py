"""Defines one deterministic top-level source unit."""

from typing import Annotated

from findings.review_unit_kind import ReviewUnitKind
from pydantic import BaseModel, ConfigDict, Field
from source.analysis.signatures.source_declaration_signature import (
    SourceDeclarationSignature,
)
from source.analysis.signatures.source_unresolved_signature import (
    SourceUnresolvedSignature,
)
from source.members.source_member import SourceMember
from source.source_line_range import SourceLineRange

SourceUnitSignature = Annotated[
    SourceDeclarationSignature | SourceUnresolvedSignature,
    Field(discriminator="kind"),
]


"""
solid-name: SourceUnit
solid-category: model
solid-spec: [SPEC-040, SPEC-062, SPEC-057]
solid-description: Records a stable top-level declaration identity, kind, name, inclusive source span, typed header, and ordered direct-member facts.
"""


class SourceUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    kind: ReviewUnitKind
    name: str = Field(min_length=1)
    span: SourceLineRange
    start_offset: int = Field(ge=0)
    end_offset: int = Field(ge=0)
    members: list[SourceMember] = Field(default_factory=list)
    signature: SourceUnitSignature = Field(default_factory=SourceUnresolvedSignature)
