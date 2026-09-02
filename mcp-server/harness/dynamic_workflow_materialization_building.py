"""Defines assembly of a complete dynamic workflow materialization."""

from typing import Protocol

from harness.dynamic_include_group_hierarchy import DynamicIncludeGroupHierarchy
from harness.dynamic_workflow_materialization import DynamicWorkflowMaterialization
from harness.include_group_tree_materialization import IncludeGroupTreeMaterialization


"""
solid-name: DynamicWorkflowMaterializationBuilding
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for combining materialized include-group trees into one dynamic workflow result.
"""
class DynamicWorkflowMaterializationBuilding(Protocol):
    def build(
        self,
        hierarchy: DynamicIncludeGroupHierarchy,
        trees: list[IncludeGroupTreeMaterialization],
    ) -> DynamicWorkflowMaterialization: ...
