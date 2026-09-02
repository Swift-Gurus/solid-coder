"""Collects distinct workflow instances from materialized steps."""

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.materialized_workflow_instances_collecting import (
    MaterializedWorkflowInstancesCollecting,
)
from harness.models import StepDef


"""
solid-name: MaterializedWorkflowInstancesCollector
solid-category: service
solid-spec: [SPEC-037]
solid-description: Collects distinct included-workflow instances in materialized step order.
"""
class MaterializedWorkflowInstancesCollector(
    MaterializedWorkflowInstancesCollecting
):
    def collect(
        self,
        steps: list[StepDef],
    ) -> list[IncludedWorkflowInstance]:
        instances: list[IncludedWorkflowInstance] = []
        for step in steps:
            instance = step.workflow_instance
            if instance is None or any(
                existing.instance_id == instance.instance_id
                for existing in instances
            ):
                continue
            instances.append(instance)
        return instances
