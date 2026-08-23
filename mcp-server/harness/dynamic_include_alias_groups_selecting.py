"""Defines selection of runtime include alias groups."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: DynamicIncludeAliasGroupsSelecting
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for selecting include groups that require runtime materialization.
"""
class DynamicIncludeAliasGroupsSelecting(Protocol):
    def select(
        self,
        groups: list[IncludeAliasGroup],
    ) -> list[IncludeAliasGroup]: ...
