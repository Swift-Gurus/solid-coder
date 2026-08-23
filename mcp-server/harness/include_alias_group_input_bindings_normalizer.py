"""Normalizes input bindings carried by one include group."""

from dataclasses import replace

from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_input_bindings_normalizing import (
    IncludeAliasGroupInputBindingsNormalizing,
)
from harness.workflow_input_binding_nested_normalizing import (
    WorkflowInputBindingNestedNormalizing,
)


"""
solid-name: IncludeAliasGroupInputBindingsNormalizer
solid-category: service
solid-spec: [SPEC-035, SPEC-037]
solid-description: Applies nested-scope normalization across an include group's typed input bindings.
"""
class IncludeAliasGroupInputBindingsNormalizer(
    IncludeAliasGroupInputBindingsNormalizing
):
    def __init__(
        self,
        binding: WorkflowInputBindingNestedNormalizing,
    ) -> None:
        self._binding = binding

    def normalize(
        self,
        group: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
    ) -> IncludeAliasGroup:
        return replace(
            group,
            input_bindings=[
                self._binding.normalize(binding, group, all_groups)
                for binding in group.input_bindings
            ],
        )
