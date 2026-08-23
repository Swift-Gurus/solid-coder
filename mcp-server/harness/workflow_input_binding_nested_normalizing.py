"""Defines nested-scope normalization of one workflow input binding."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.workflow_input_binding import WorkflowInputBinding


"""
solid-name: WorkflowInputBindingNestedNormalizing
solid-category: abstraction
solid-spec: [SPEC-035, SPEC-037]
solid-description: Contract for normalizing one workflow input binding against its nested include scope.
"""
class WorkflowInputBindingNestedNormalizing(Protocol):
    def normalize(
        self,
        binding: WorkflowInputBinding,
        group: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
    ) -> WorkflowInputBinding: ...
