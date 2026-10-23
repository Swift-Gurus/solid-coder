"""Defines immutable member extension for include-alias groups."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup

"""
solid-name: IncludeAliasGroupMembersAppending
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for appending expanded step identifiers to an include-alias group.
"""


class IncludeAliasGroupMembersAppending(Protocol):
    def append_members(
        self,
        group: IncludeAliasGroup,
        member_ids: list[str],
    ) -> IncludeAliasGroup: ...
