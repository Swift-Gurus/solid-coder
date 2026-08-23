"""Assembles dynamic include groups with normalized iteration sources."""

from harness.dynamic_include_alias_groups_assembling import (
    DynamicIncludeAliasGroupsAssembling,
)
from harness.dynamic_include_alias_groups_selecting import (
    DynamicIncludeAliasGroupsSelecting,
)
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_for_each_normalizing import (
    IncludeAliasGroupForEachNormalizing,
)
from harness.include_alias_group_input_bindings_normalizing import (
    IncludeAliasGroupInputBindingsNormalizing,
)


"""
solid-name: DynamicIncludeAliasGroupsAssembler
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Produces runtime include groups with normalized typed iteration sources.
"""
class DynamicIncludeAliasGroupsAssembler(
    DynamicIncludeAliasGroupsAssembling
):
    def __init__(
        self,
        selector: DynamicIncludeAliasGroupsSelecting,
        for_each: IncludeAliasGroupForEachNormalizing,
        input_bindings: IncludeAliasGroupInputBindingsNormalizing,
    ) -> None:
        self._selector = selector
        self._for_each = for_each
        self._input_bindings = input_bindings

    def assemble(
        self,
        groups: list[IncludeAliasGroup],
    ) -> list[IncludeAliasGroup]:
        return [
            self._input_bindings.normalize(
                self._for_each.normalize(group, groups),
                groups,
            )
            for group in self._selector.select(groups)
        ]
