"""Defines materialization of one dynamic include group and its descendants."""

from __future__ import annotations

from typing import Protocol

from harness.include_alias_group import IncludeAliasGroup
from harness.include_group_tree_materialization import IncludeGroupTreeMaterialization
from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import FlowDef, RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: DynamicIncludeGroupMaterializing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for materializing one dynamic include group and all descendants owned by its runtime instances.
"""
class DynamicIncludeGroupMaterializing(Protocol):
    def materialize(
        self,
        group: IncludeAliasGroup,
        owner_group: IncludeAliasGroup | None,
        owner_instance: IncludedWorkflowInstance | None,
        all_groups: list[IncludeAliasGroup],
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> IncludeGroupTreeMaterialization: ...
