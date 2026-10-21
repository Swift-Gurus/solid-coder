"""Checks whether a ready step may begin an aggregate model phase."""

from __future__ import annotations

from harness.aggregate_step_eligibility_checking import AggregateStepEligibilityChecking
from harness.batch_step_presentation_mode import BatchStepPresentationMode
from harness.flow_def import FlowDef
from harness.for_each_mode import ForEachMode
from harness.step_def import StepDef
from harness.step_instance import StepInstance
from harness.workflow_execution_mode import WorkflowExecutionMode
from harness.workflow_presentation_mode import WorkflowPresentationMode


_MODEL_OWNED_STEP_TYPES = frozenset({"agent", "metric", "exception"})


"""
solid-name: AggregateStepEligibilityChecker
solid-category: service
solid-spec: [SPEC-045]
solid-description: Selects steps eligible for aggregate model execution.
"""
class AggregateStepEligibilityChecker(AggregateStepEligibilityChecking):
    def is_eligible(
        self,
        flow: FlowDef,
        instance: StepInstance,
        step: StepDef,
    ) -> bool:
        execution = flow.execution
        presentation = flow.presentation
        if instance.workflow_instance is not None:
            execution = instance.workflow_instance.execution
            presentation = instance.workflow_instance.presentation
        combined = (
            presentation is WorkflowPresentationMode.COMBINED
            and (
                instance.batch is None
                or instance.batch.mode is not BatchStepPresentationMode.COMBINED_RULES
                or instance.workflow_instance is not None
                and len(instance.workflow_instance.steps.entries) > 1
            )
        )
        return (
            (execution is WorkflowExecutionMode.AGGREGATE or combined)
            and step.type in _MODEL_OWNED_STEP_TYPES
            and not (
                step.for_each is not None
                and step.for_each.mode is ForEachMode.INDIVIDUAL
                and (step.for_each.mode_declared or (instance.workflow_instance is not None and not combined))
            )
        )
