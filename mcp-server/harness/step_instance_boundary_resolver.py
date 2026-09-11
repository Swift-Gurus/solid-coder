"""Resolves workflow ownership for a ready step instance."""

from __future__ import annotations

from harness.flow_def import FlowDef
from harness.step_instance import StepInstance
from harness.step_instance_boundary_resolving import StepInstanceBoundaryResolving


"""
solid-name: StepInstanceBoundaryResolver
solid-category: service
solid-spec: [SPEC-045]
solid-description: Identifies the workflow boundary that owns a ready step instance.
"""
class StepInstanceBoundaryResolver(StepInstanceBoundaryResolving):
    def resolve(self, flow: FlowDef, instance: StepInstance) -> str:
        if instance.workflow_instance is not None:
            return instance.workflow_instance.instance_id
        return flow.workflow_id
