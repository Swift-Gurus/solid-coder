"""Defines assembly of runtime include alias groups."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: DynamicIncludeAliasGroupsAssembling
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for selecting dynamic include groups and normalizing their typed runtime references.
"""
class DynamicIncludeAliasGroupsAssembling(Protocol):
    def assemble(
        self,
        groups: list[IncludeAliasGroup],
    ) -> list[IncludeAliasGroup]: ...
