"""Defines immutable include-group replacement."""

from __future__ import annotations

from typing import Protocol

from harness.combined_rule_presentation import CombinedRulePresentation
from harness.include_alias_group import IncludeAliasGroup
from harness.nested_include_child_group_policy import NestedIncludeChildGroupPolicy


"""
solid-name: IncludeAliasGroupReplacing
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Contract for replacing nested include-group policy while preserving its remaining fields.
"""
class IncludeAliasGroupReplacing(Protocol):
    def replace_policy(
        self,
        group: IncludeAliasGroup,
        policy: NestedIncludeChildGroupPolicy,
        presentation: CombinedRulePresentation | None,
    ) -> IncludeAliasGroup: ...
