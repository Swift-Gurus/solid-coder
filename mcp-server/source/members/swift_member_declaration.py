"""Decodes member-relevant fields at the external Swift parser boundary."""

from __future__ import annotations

from typing import Optional

from pydantic import AliasChoices, AliasPath, BaseModel, ConfigDict, Field

from source.members.swift_access_attribute import SwiftAccessAttribute


"""
solid-name: SwiftMemberDeclaration
solid-category: model
solid-spec: [SPEC-062]
solid-description: Represents member-relevant syntax facts at the parser boundary while preserving absent ranges for partial declarations.
"""
class SwiftMemberDeclaration(BaseModel):
    model_config = ConfigDict(extra="ignore", frozen=True)

    kind: str = Field(alias="_kind")
    name: str = Field(
        default="",
        validation_alias=AliasChoices(
            AliasPath("name", "base_name", "name"),
            AliasPath("name", "base_name", "special"),
        ),
    )
    start_offset: Optional[int] = Field(default=None, validation_alias=AliasPath("range", "start"))
    end_offset: Optional[int] = Field(default=None, validation_alias=AliasPath("range", "end"))
    implicit: bool = False
    attributes: list[SwiftAccessAttribute] = Field(default_factory=list, validation_alias="attrs")
    members: list[SwiftMemberDeclaration] = Field(default_factory=list)
