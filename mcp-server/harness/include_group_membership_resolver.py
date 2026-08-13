"""Resolves include-group memberships for a step."""

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_membership_resolving import IncludeGroupMembershipResolving


"""
solid-name: IncludeGroupMembershipResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Finds every include group that contains a workflow step.
"""
class IncludeGroupMembershipResolver(IncludeGroupMembershipResolving):

    def resolve(
        self,
        step_id: str,
        alias_groups: list[IncludeAliasGroup],
    ) -> set[str]:
        return {
            group.alias
            for group in alias_groups
            if group.contains(step_id)
        }
