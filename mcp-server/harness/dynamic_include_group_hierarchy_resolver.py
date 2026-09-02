"""Resolves dynamic include groups and their executable roots."""

from harness.dynamic_include_group_hierarchy import DynamicIncludeGroupHierarchy
from harness.dynamic_include_group_hierarchy_resolving import (
    DynamicIncludeGroupHierarchyResolving,
)
from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking


"""
solid-name: DynamicIncludeGroupHierarchyResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Selects dynamic include groups and roots whose owners are not dynamically materialized.
"""
class DynamicIncludeGroupHierarchyResolver(
    DynamicIncludeGroupHierarchyResolving
):
    def __init__(self, dynamic_checker: IncludeGroupDynamicChecking) -> None:
        self._dynamic_checker = dynamic_checker

    def resolve(
        self,
        groups: list[IncludeAliasGroup],
    ) -> DynamicIncludeGroupHierarchy:
        dynamic_groups = [
            group
            for group in groups
            if self._dynamic_checker.is_dynamic(group)
        ]
        return DynamicIncludeGroupHierarchy(
            groups=dynamic_groups,
            roots=[
                group
                for group in dynamic_groups
                if group.owner_alias is None
                or not any(
                    candidate.alias == group.owner_alias
                    for candidate in dynamic_groups
                )
            ],
        )
