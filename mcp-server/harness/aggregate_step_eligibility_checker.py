"""Checks whether a ready step may begin an aggregate model phase."""

from __future__ import annotations

from harness.aggregate_step_eligibility_checking import AggregateStepEligibilityChecking
from harness.flow_def import FlowDef
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.workflow_execution_mode import WorkflowExecutionMode


_MODEL_OWNED_STEP_TYPES = frozenset({"agent", "metric", "exception"})


"""
solid-name: AggregateStepEligibilityChecker
solid-category: service
solid-spec: [SPEC-045]
solid-description: Determines aggregate eligibility from typed ownership policy and step execution type.
"""
class AggregateStepEligibilityChecker(AggregateStepEligibilityChecking):
    def is_eligible(
        self,
        flow: FlowDef,
        instance: StepInstance,
        step: StepDef,
    ) -> bool:
        execution = flow.execution
        if instance.workflow_instance is not None:
            execution = instance.workflow_instance.execution
        return (
            execution is WorkflowExecutionMode.AGGREGATE
            and step.type in _MODEL_OWNED_STEP_TYPES
        )
