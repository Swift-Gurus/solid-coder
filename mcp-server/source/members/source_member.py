"""Defines one direct source member with deterministic source evidence."""

from pydantic import BaseModel, ConfigDict, Field

from source.members.source_member_kind import SourceMemberKind
from source.members.source_member_visibility import SourceMemberVisibility
from source.source_line_range import SourceLineRange


"""
solid-name: SourceMember
solid-category: model
solid-spec: [SPEC-062]
solid-description: Records an ordered declaration member with stable identity, kind, visibility, and source line evidence for downstream workflow selection.
"""
class SourceMember(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    name: str = Field(min_length=1)
    kind: SourceMemberKind
    visibility: SourceMemberVisibility
    span: SourceLineRange
