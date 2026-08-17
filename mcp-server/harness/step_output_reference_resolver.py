"""Resolves typed local step-output references."""

from typing import Generic, TypeVar, cast

from harness.interpolation_error_creating import InterpolationErrorCreating
from harness.step_output_reference import StepOutputReference
from harness.workflow_run_context import WorkflowRunContext


Value = TypeVar("Value")


"""
solid-name: StepOutputReferenceResolver
solid-category: service
solid-spec: [SPEC-030, SPEC-037]
solid-description: Resolves a typed local step-output reference from the completed outputs visible in one workflow scope.
"""
class StepOutputReferenceResolver(Generic[Value]):
    def __init__(self, error_factory: InterpolationErrorCreating) -> None:
        self._error_factory = error_factory

    def resolve(
        self,
        reference: StepOutputReference,
        context: WorkflowRunContext,
    ) -> Value:
        expression = (
            f"steps.{reference.step_id}.outputs.{reference.output_name}"
        )
        completed_step = context.completed_steps.find(reference.step_id)
        if not completed_step.present or completed_step.value is None:
            raise self._error_factory.create(expression)
        value = completed_step.value.get(reference.output_name)
        if value is None:
            raise self._error_factory.create(expression)
        return cast(Value, value)
