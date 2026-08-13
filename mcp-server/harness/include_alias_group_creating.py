"""Defines creation of typed workflow include-alias groups."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupCreating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for creating a workflow include alias with its member-step identifiers.
"""
class IncludeAliasGroupCreating(Protocol):

    def create(self, alias: str, member_ids: list[str]) -> IncludeAliasGroup: ...
