"""Coordinates optional batch presentation resolution."""

from __future__ import annotations

from harness.batch_step_presentation import BatchStepPresentation
from harness.batch_step_presentation_building import BatchStepPresentationBuilding
from harness.batch_step_presentation_resolving import (
    BatchStepPresentationResolving,
)
from harness.for_each_mode import ForEachMode
from harness.models import StepDef
from harness.step_for_each_declaration_resolving import (
    StepForEachDeclarationResolving,
)
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: BatchStepPresentationResolver
solid-category: service
solid-spec: [SPEC-042]
solid-description: Coordinates effective iteration lookup and construction only for explicitly batched model presentation.
"""
class BatchStepPresentationResolver(BatchStepPresentationResolving):
    def __init__(
        self,
        declaration_resolver: StepForEachDeclarationResolving,
        presentation_builder: BatchStepPresentationBuilding,
    ) -> None:
        self._declaration_resolver = declaration_resolver
        self._presentation_builder = presentation_builder

    def resolve(
        self,
        step: StepDef,
        context: WorkflowRunContext,
    ) -> BatchStepPresentation | None:
        declaration = self._declaration_resolver.resolve(step)
        if declaration is None or declaration.mode is ForEachMode.INDIVIDUAL:
            return None
        return self._presentation_builder.build(step, declaration, context)
