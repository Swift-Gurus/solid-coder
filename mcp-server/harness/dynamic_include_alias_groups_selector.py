"""Selects include groups requiring runtime materialization."""

from harness.dynamic_include_alias_groups_selecting import (
    DynamicIncludeAliasGroupsSelecting,
)
from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking


"""
solid-name: DynamicIncludeAliasGroupsSelector
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Applies the configured dynamic-group policy to an authored include collection.
"""
class DynamicIncludeAliasGroupsSelector(
    DynamicIncludeAliasGroupsSelecting
):
    def __init__(
        self,
        dynamic_checker: IncludeGroupDynamicChecking,
    ) -> None:
        self._dynamic_checker = dynamic_checker

    def select(
        self,
        groups: list[IncludeAliasGroup],
    ) -> list[IncludeAliasGroup]:
        return [
            group
            for group in groups
            if self._dynamic_checker.is_dynamic(group)
        ]
