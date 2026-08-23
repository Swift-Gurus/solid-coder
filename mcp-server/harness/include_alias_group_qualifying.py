"""Defines alias qualification of a nested include group."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeAliasGroupQualifying
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for qualifying nested group identity, dependencies, members, and typed iteration source.
"""
class IncludeAliasGroupQualifying(Protocol):
    def qualify(
        self,
        alias: str,
        group: IncludeAliasGroup,
        local_dependency_ids: set[str],
    ) -> IncludeAliasGroup: ...
