"""Defines recursive expansion of one dynamic include-group root."""

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_tree_materialization import IncludeGroupTreeMaterialization
from harness.models import FlowDef, RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: DynamicIncludeGroupExpanding
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for recursively materializing one dynamic include-group root and its owned descendants.
"""
class DynamicIncludeGroupExpanding(Protocol):
    def expand(
        self,
        root: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> IncludeGroupTreeMaterialization: ...
