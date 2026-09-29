"""Adapts dataclass replacement to include-group member extension."""

from dataclasses import replace

from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_members_appending import (
    IncludeAliasGroupMembersAppending,
)


"""
solid-name: DataclassIncludeAliasGroupMembersAppender
solid-category: adapter
solid-spec: [SPEC-058]
solid-description: Appends expanded step identifiers while preserving remaining include-group information.
"""
class DataclassIncludeAliasGroupMembersAppender(
    IncludeAliasGroupMembersAppending,
):
    def append_members(
        self,
        group: IncludeAliasGroup,
        member_ids: list[str],
    ) -> IncludeAliasGroup:
        return replace(
            group,
            member_ids=[*group.member_ids, *member_ids],
        )
