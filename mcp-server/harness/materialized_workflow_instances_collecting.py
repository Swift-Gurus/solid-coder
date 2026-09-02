"""Defines collection of workflow instances from materialized steps."""

from typing import Protocol

from harness.included_workflow_instance import IncludedWorkflowInstance
from harness.models import StepDef


"""
solid-name: MaterializedWorkflowInstancesCollecting
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for collecting distinct included-workflow instances from materialized steps.
"""
class MaterializedWorkflowInstancesCollecting(Protocol):
    def collect(
        self,
        steps: list[StepDef],
    ) -> list[IncludedWorkflowInstance]: ...
