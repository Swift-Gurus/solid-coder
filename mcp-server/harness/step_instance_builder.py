"""Materializes executable step instances from typed runtime context."""

from __future__ import annotations

from harness.interpolator import TemplateRendering
from harness.models import StepDef, StepInstance
from harness.operation_inputs_resolving import OperationInputsResolving
from harness.operation_step_instance import OperationStepInstance
from harness.step_instance_building import StepInstanceBuilding
from harness.workflow_run_context import WorkflowRunContext
from harness.workflow_step_context_resolving import WorkflowStepContextResolving


"""
solid-name: StepInstanceBuilder
solid-category: service
solid-spec: [SPEC-010, SPEC-030, SPEC-037, SPEC-040]
solid-description: Materializes ordinary or operation-specific step instances from resolved runtime context.
"""
class StepInstanceBuilder(StepInstanceBuilding):
    def __init__(
        self,
        renderer: TemplateRendering,
        context_resolver: WorkflowStepContextResolving,
        operation_inputs_resolver: OperationInputsResolving,
    ) -> None:
        self._renderer = renderer
        self._context_resolver = context_resolver
        self._operation_inputs_resolver = operation_inputs_resolver

    def build(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        item: object,
        instance_id: str,
        iteration_index: int | None = None,
    ) -> StepInstance:
        step_context = self._context_resolver.resolve(
            context,
            step.workflow_instance,
            item,
        )
        prompt = self._renderer.render(step.prompt, step_context)
        if step.operation is None:
            return StepInstance(
                step_id=step.id,
                instance_id=instance_id,
                item=item,
                prompt=prompt,
                iteration_index=iteration_index,
                workflow_instance=step.workflow_instance,
            )
        return OperationStepInstance(
            step_id=step.id,
            instance_id=instance_id,
            item=item,
            prompt=prompt,
            iteration_index=iteration_index,
            workflow_instance=step.workflow_instance,
            inputs=self._operation_inputs_resolver.resolve(
                step.operation,
                step_context,
            ),
        )
