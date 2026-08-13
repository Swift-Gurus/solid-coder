"""Creates typed workflow include-alias groups."""

from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_creating import IncludeAliasGroupCreating


"""
solid-name: IncludeAliasGroupFactory
solid-category: factory
solid-spec: [SPEC-027, SPEC-035]
solid-description: Creates a workflow include alias with its member-step identifiers.
"""
class IncludeAliasGroupFactory(IncludeAliasGroupCreating):

    def create(self, alias: str, member_ids: list[str]) -> IncludeAliasGroup:
        return IncludeAliasGroup(alias=alias, member_ids=member_ids)
