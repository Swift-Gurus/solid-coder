"""Qualifies one nested include group under its owning alias."""

from dataclasses import replace

from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_qualifying import IncludeAliasGroupQualifying
from harness.nested_identity_qualifying import NestedIdentityQualifying


"""
solid-name: NestedIncludeAliasGroupQualifier
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Prefixes nested group identities and typed local references while preserving external references.
"""
class NestedIncludeAliasGroupQualifier(IncludeAliasGroupQualifying):
    def __init__(
        self,
        identity: NestedIdentityQualifying,
    ) -> None:
        self._identity = identity

    def qualify(
        self,
        alias: str,
        group: IncludeAliasGroup,
        local_dependency_ids: set[str],
    ) -> IncludeAliasGroup:
        return replace(
            group,
            alias=f"{alias}.{group.alias}",
            member_ids=[f"{alias}.{member}" for member in group.member_ids],
            depends_on=[
                self._identity.qualify(
                    alias,
                    dependency,
                    local_dependency_ids,
                )
                for dependency in group.depends_on
            ],
        )
