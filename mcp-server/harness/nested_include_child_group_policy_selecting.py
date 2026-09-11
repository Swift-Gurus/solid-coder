"""Defines nested child-group policy selection."""

from __future__ import annotations

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.include_source import IncludeSource
from harness.nested_include_child_group_policy import NestedIncludeChildGroupPolicy


"""
solid-name: NestedIncludeChildGroupPolicySelecting
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Contract for selecting effective ownership and execution policy for a nested child group.
"""
class NestedIncludeChildGroupPolicySelecting(Protocol):
    def select(
        self,
        group: IncludeAliasGroup,
        source: IncludeSource,
        transparent_aliases: set[str],
    ) -> NestedIncludeChildGroupPolicy | None: ...
