"""Defines runtime resolution of typed step-output references."""

from typing import Generic, Protocol, TypeVar

from harness.step_output_reference import StepOutputReference
from harness.workflow_run_context import WorkflowRunContext


Value = TypeVar("Value")


"""
solid-name: StepOutputReferenceResolving
solid-category: abstraction
solid-spec: [SPEC-030, SPEC-037]
solid-description: Contract for resolving one typed local step-output reference against a workflow execution context.
"""
class StepOutputReferenceResolving(Protocol, Generic[Value]):
    def resolve(
        self,
        reference: StepOutputReference,
        context: WorkflowRunContext,
    ) -> Value: ...
