"""Defines resolution of include-group memberships for a step."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: IncludeGroupMembershipResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for finding every include group that contains a workflow step.
"""
class IncludeGroupMembershipResolving(Protocol):

    def resolve(
        self,
        step_id: str,
        alias_groups: list[IncludeAliasGroup],
    ) -> set[str]: ...
