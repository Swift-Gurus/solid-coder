"""Defines construction of one batched step presentation item."""

from typing import Protocol

from harness.batch_step_presentation import BatchStepPresentation
from harness.for_each_declaration import ForEachDeclaration
from harness.models import StepDef
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: BatchStepPresentationBuilding
solid-category: abstraction
solid-spec: [SPEC-042]
solid-description: Contract for constructing compact batch group and label identity from a resolved iteration declaration.
"""
class BatchStepPresentationBuilding(Protocol):
    def build(
        self,
        step: StepDef,
        declaration: ForEachDeclaration,
        context: WorkflowRunContext,
    ) -> BatchStepPresentation: ...
