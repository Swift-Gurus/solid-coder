"""Resolves materialized included-workflow instances by alias."""

from __future__ import annotations

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.included_workflow_instances_resolving import (
    IncludedWorkflowInstancesResolving,
)
from harness.models import FlowDef


"""
solid-name: IncludedWorkflowInstancesResolver
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves ordered materialized workflow instances owned by one include alias.
"""
class IncludedWorkflowInstancesResolver(IncludedWorkflowInstancesResolving):
    def resolve(
        self,
        flow: FlowDef,
        alias: str,
    ) -> list[IncludedWorkflowInstance]:
        instances: list[IncludedWorkflowInstance] = []
        for step in flow.steps:
            instance = step.workflow_instance
            if instance is None or instance.alias != alias:
                continue
            if any(
                existing.instance_id == instance.instance_id
                for existing in instances
            ):
                continue
            instances.append(instance)
        return sorted(instances, key=lambda instance: instance.source_index)
