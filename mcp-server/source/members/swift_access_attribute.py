"""Captures declaration access attributes at the Swift parser boundary."""

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from source.members.source_member_visibility import SourceMemberVisibility


"""
solid-name: SwiftAccessAttribute
solid-category: model
solid-spec: [SPEC-062]
solid-description: Captures external declaration access attributes without treating setter-only access as declaration visibility.
"""
class SwiftAccessAttribute(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    kind: str = Field(alias="_kind")
    access_level: Optional[SourceMemberVisibility] = None
