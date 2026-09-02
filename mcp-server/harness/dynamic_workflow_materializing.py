"""Defines runtime materialization of dynamic workflow groups."""

from typing import Protocol

from harness.dynamic_workflow_materialization import DynamicWorkflowMaterialization
from harness.models import FlowDef, RunState
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: DynamicWorkflowMaterializing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for materializing dynamic include-group hierarchies for one workflow snapshot.
"""
class DynamicWorkflowMaterializing(Protocol):
    def materialize(
        self,
        flow: FlowDef,
        run_state: RunState,
        context: WorkflowRunContext,
    ) -> DynamicWorkflowMaterialization: ...
