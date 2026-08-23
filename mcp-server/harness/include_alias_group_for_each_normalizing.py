"""Defines normalization of one include group's iteration source."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupForEachNormalizing
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for resolving a group's typed iteration source against the complete include hierarchy.
"""
class IncludeAliasGroupForEachNormalizing(Protocol):
    def normalize(
        self,
        group: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup: ...
