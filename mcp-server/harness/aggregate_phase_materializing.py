"""Declares aggregate phase instance materialization."""

from typing import Protocol

from harness.aggregate_phase import AggregateExpansion, AggregatePhase
from harness.flow_def import FlowDef
from harness.step_instance import StepInstance
from harness.workflow_run_context import WorkflowRunContext

"""
solid-name: AggregatePhaseMaterializing
solid-category: abstraction
solid-spec: [SPEC-045]
solid-description: Contract for expanding aggregate workflow phases into executable steps.
"""


class AggregatePhaseMaterializing(Protocol):
    def materialize(
        self,
        flow: FlowDef,
        phase: AggregatePhase,
        ready: list[StepInstance],
        context: WorkflowRunContext,
    ) -> AggregateExpansion: ...
