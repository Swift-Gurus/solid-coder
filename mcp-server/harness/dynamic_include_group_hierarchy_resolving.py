"""Defines resolution of the dynamic include-group hierarchy."""

from typing import Protocol

from harness.dynamic_include_group_hierarchy import DynamicIncludeGroupHierarchy
from harness.include_alias_group import IncludeAliasGroup


"""
solid-name: DynamicIncludeGroupHierarchyResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for selecting dynamic include groups and their executable hierarchy roots.
"""
class DynamicIncludeGroupHierarchyResolving(Protocol):
    def resolve(
        self,
        groups: list[IncludeAliasGroup],
    ) -> DynamicIncludeGroupHierarchy: ...
