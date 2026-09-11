"""Adapts dataclass replacement to include-group policy replacement."""

from __future__ import annotations

from dataclasses import replace

from harness.combined_rule_presentation import CombinedRulePresentation
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_replacing import IncludeAliasGroupReplacing
from harness.nested_include_child_group_policy import NestedIncludeChildGroupPolicy


"""
solid-name: DataclassIncludeAliasGroupReplacer
solid-category: adapter
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Applies nested include-group policy updates while preserving remaining group information.
"""
class DataclassIncludeAliasGroupReplacer(IncludeAliasGroupReplacing):
    def replace_policy(
        self,
        group: IncludeAliasGroup,
        policy: NestedIncludeChildGroupPolicy,
        presentation: CombinedRulePresentation | None,
    ) -> IncludeAliasGroup:
        return replace(
            group,
            owner_alias=policy.owner_alias,
            execution=policy.execution,
            combined_presentation=presentation,
        )
