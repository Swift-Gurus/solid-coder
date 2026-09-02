"""Combines materialized include-group trees into one workflow result."""

from harness.dynamic_include_group_hierarchy import DynamicIncludeGroupHierarchy
from harness.dynamic_workflow_materialization import DynamicWorkflowMaterialization
from harness.dynamic_workflow_materialization_building import (
    DynamicWorkflowMaterializationBuilding,
)
from harness.include_group_tree_materialization import IncludeGroupTreeMaterialization


"""
solid-name: DynamicWorkflowMaterializationBuilder
solid-category: service
solid-spec: [SPEC-037]
solid-description: Combines ordered dynamic include-group tree results and authored membership identities.
"""
class DynamicWorkflowMaterializationBuilder(
    DynamicWorkflowMaterializationBuilding
):
    def build(
        self,
        hierarchy: DynamicIncludeGroupHierarchy,
        trees: list[IncludeGroupTreeMaterialization],
    ) -> DynamicWorkflowMaterialization:
        return DynamicWorkflowMaterialization(
            steps=[step for tree in trees for step in tree.steps],
            groups=[group for tree in trees for group in tree.groups],
            authored_group_aliases={
                group.alias for group in hierarchy.groups
            },
            authored_member_ids={
                member_id
                for group in hierarchy.groups
                for member_id in group.member_ids
            },
        )
