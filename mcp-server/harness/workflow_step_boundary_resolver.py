"""Resolves workflow ownership for a resolved step."""

from __future__ import annotations

from harness.flow_def import FlowDef
from harness.step_def import StepDef
from harness.workflow_step_boundary_resolving import WorkflowStepBoundaryResolving


"""
solid-name: WorkflowStepBoundaryResolver
solid-category: service
solid-spec: [SPEC-045]
solid-description: Identifies the workflow boundary that owns a resolved step.
"""
class WorkflowStepBoundaryResolver(WorkflowStepBoundaryResolving):
    def resolve(self, flow: FlowDef, step: StepDef) -> str:
        if step.workflow_instance is not None:
            return step.workflow_instance.instance_id
        return flow.workflow_id
