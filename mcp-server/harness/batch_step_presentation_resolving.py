"""Defines resolution of optional batch presentation identity."""

from typing import Optional, Protocol

from harness.batch_step_presentation import BatchStepPresentation
from harness.models import StepDef
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: BatchStepPresentationResolving
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for resolving one ready step's batch group and domain label from typed workflow context.
"""
class BatchStepPresentationResolving(Protocol):
    def resolve(
        self,
        step: StepDef,
        context: WorkflowRunContext,
    ) -> Optional[BatchStepPresentation]: ...
