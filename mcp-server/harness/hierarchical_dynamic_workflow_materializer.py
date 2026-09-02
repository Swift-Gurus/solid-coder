"""Coordinates materialization of all dynamic include-group roots."""

from harness.dynamic_include_group_expanding import DynamicIncludeGroupExpanding
from harness.dynamic_include_group_hierarchy_resolving import (
    DynamicIncludeGroupHierarchyResolving,
)
from harness.dynamic_workflow_materialization import DynamicWorkflowMaterialization
from harness.dynamic_workflow_materialization_building import (
    DynamicWorkflowMaterializationBuilding,
)
from harness.dynamic_workflow_materializing import DynamicWorkflowMaterializing
from harness.models import FlowDef, RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: HierarchicalDynamicWorkflowMaterializer
solid-category: service
solid-spec: [SPEC-037]
solid-description: Coordinates ordered materialization of every dynamic include-group hierarchy root.
"""
class HierarchicalDynamicWorkflowMaterializer(DynamicWorkflowMaterializing):
    def __init__(
        self,
        hierarchy_resolver: DynamicIncludeGroupHierarchyResolving,
        group_expander: DynamicIncludeGroupExpanding,
        result_builder: DynamicWorkflowMaterializationBuilding,
    ) -> None:
        self._hierarchy_resolver = hierarchy_resolver
        self._group_expander = group_expander
        self._result_builder = result_builder

    def materialize(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> DynamicWorkflowMaterialization:
        hierarchy = self._hierarchy_resolver.resolve(flow.alias_groups)
        return self._result_builder.build(
            hierarchy,
            [
                self._group_expander.expand(
                    root,
                    hierarchy.groups,
                    flow,
                    run_state,
                    context,
                )
                for root in hierarchy.roots
            ],
        )
