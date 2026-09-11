"""Selects effective policy for one nested child group."""

from __future__ import annotations

from harness.include_alias_group import IncludeAliasGroup
from harness.include_source import IncludeSource
from harness.nested_include_child_group_policy import NestedIncludeChildGroupPolicy
from harness.nested_include_child_group_policy_selecting import (
    NestedIncludeChildGroupPolicySelecting,
)
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: NestedIncludeChildGroupPolicySelector
solid-category: service
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Resolves nested ownership and inherited inline-group execution policy.
"""
class NestedIncludeChildGroupPolicySelector(
    NestedIncludeChildGroupPolicySelecting
):
    def select(
        self,
        group: IncludeAliasGroup,
        source: IncludeSource,
        transparent_aliases: set[str],
    ) -> NestedIncludeChildGroupPolicy | None:
        owns_group = (
            group.owner_alias is None and group.alias not in transparent_aliases
        ) or group.owner_alias in transparent_aliases
        presents_group = (
            group.owner_alias is None
            and source.runtime.presentation is WorkflowPresentationMode.COMBINED
        )
        if not owns_group and not presents_group:
            return None
        execution = group.execution
        if (
            source.propagates_policy
            and source.runtime.execution is WorkflowExecutionMode.AGGREGATE
        ):
            execution = WorkflowExecutionMode.AGGREGATE
        return NestedIncludeChildGroupPolicy(
            owner_alias=source.alias if owns_group else group.owner_alias,
            execution=execution,
            combines_presentation=(
                presents_group
                or owns_group
                and source.runtime.presentation is WorkflowPresentationMode.COMBINED
            ),
        )
