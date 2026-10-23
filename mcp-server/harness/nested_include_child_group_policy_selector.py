"""Selects effective policy for one nested child group."""

from __future__ import annotations

from harness.for_each_mode import ForEachMode
from harness.include_alias_group import IncludeAliasGroup
from harness.include_source import IncludeSource
from harness.nested_include_child_group_policy import NestedIncludeChildGroupPolicy
from harness.nested_include_child_group_policy_selecting import (
    NestedIncludeChildGroupPolicySelecting,
)
from harness.workflow_presentation_mode import WorkflowPresentationMode

"""
solid-name: NestedIncludeChildGroupPolicySelector
solid-category: service
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Resolves nested ownership and inherited inline-group execution policy.
"""


class NestedIncludeChildGroupPolicySelector(NestedIncludeChildGroupPolicySelecting):
    def select(
        self,
        group: IncludeAliasGroup,
        source: IncludeSource,
        transparent_aliases: set[str],
        groups: list[IncludeAliasGroup],
    ) -> NestedIncludeChildGroupPolicy | None:
        owns_group = (
            group.owner_alias is None and group.alias not in transparent_aliases
        ) or group.owner_alias in transparent_aliases
        combines = source.runtime.presentation is WorkflowPresentationMode.COMBINED
        ancestor: IncludeAliasGroup | None = group
        visited: set[str] = set()
        while ancestor is not None and ancestor.alias not in visited:
            visited.add(ancestor.alias)
            combines = combines and (
                ancestor.presentation is WorkflowPresentationMode.COMBINED
                and not (
                    ancestor.for_each is not None
                    and ancestor.for_each.mode_declared
                    and ancestor.for_each.mode is ForEachMode.INDIVIDUAL
                )
            )
            ancestor = next(
                (
                    candidate
                    for candidate in groups
                    if candidate.alias == ancestor.owner_alias
                ),
                None,
            )
        return NestedIncludeChildGroupPolicy(
            owner_alias=source.alias if owns_group else group.owner_alias,
            execution=group.execution,
            presentation=group.presentation,
            execution_declared=group.execution_declared,
            presentation_declared=group.presentation_declared,
            combines_presentation=combines,
        )
