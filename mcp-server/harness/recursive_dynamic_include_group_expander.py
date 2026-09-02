"""Starts recursive expansion for one dynamic include-group root."""

from harness.dynamic_include_group_expanding import DynamicIncludeGroupExpanding
from harness.dynamic_include_group_materializing import DynamicIncludeGroupMaterializing
from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_tree_materialization import IncludeGroupTreeMaterialization
from harness.models import FlowDef, RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: RecursiveDynamicIncludeGroupExpander
solid-category: service
solid-spec: [SPEC-037]
solid-description: Starts recursive materialization for one dynamic include-group hierarchy root.
"""
class RecursiveDynamicIncludeGroupExpander(DynamicIncludeGroupExpanding):
    def __init__(
        self,
        group_materializer: DynamicIncludeGroupMaterializing,
    ) -> None:
        self._group_materializer = group_materializer

    def expand(
        self,
        root: IncludeAliasGroup,
        all_groups: list[IncludeAliasGroup],
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> IncludeGroupTreeMaterialization:
        return self._group_materializer.materialize(
            group=root,
            owner_group=None,
            owner_instance=None,
            all_groups=all_groups,
            flow=flow,
            run_state=run_state,
            context=context,
        )
