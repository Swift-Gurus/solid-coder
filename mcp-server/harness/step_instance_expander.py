"""Expands ready workflow declarations into executable instances."""

from __future__ import annotations

from dataclasses import replace

from harness.for_each_items_resolving import ForEachItemsResolving
from harness.interpolator import TemplateRendering
from harness.models import RunState, StepDef, StepInstance, StepOutputs
from harness.resolved_workflow_context_value import ResolvedWorkflowContextValue
from harness.step_instance_expanding import StepInstanceExpanding
from harness.workflow_run_context import WorkflowRunContext


"""
solid-name: StepInstanceExpander
solid-category: service
solid-spec: [SPEC-010, SPEC-030, SPEC-037]
solid-description: Coordinates ordered workflow iteration expansion while excluding terminal instances.
"""
class StepInstanceExpander(StepInstanceExpanding):
    def __init__(
        self,
        items_resolver: ForEachItemsResolving,
        renderer: TemplateRendering,
    ) -> None:
        self._items_resolver = items_resolver
        self._renderer = renderer

    def expand(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        run_state: RunState,
    ) -> list[StepInstance]:
        if step.for_each is None:
            return [
                StepInstance(
                    step_id=step.id,
                    instance_id=f"{step.id}-1",
                    item=(
                        step.workflow_instance.source_item
                        if step.workflow_instance is not None
                        else None
                    ),
                    prompt=self._renderer.render(step.prompt, context),
                    workflow_instance=step.workflow_instance,
                )
            ]

        items = self._items_resolver.resolve(
            step.id,
            step.for_each,
            context,
        )
        if not items:
            return [
                StepInstance(
                    step_id=step.id,
                    instance_id=f"{step.id}-0",
                    item=None,
                    prompt="",
                    iteration_index=0,
                    automatic_outputs=StepOutputs(
                        values={output.name: [] for output in step.outputs}
                    ),
                    workflow_instance=step.workflow_instance,
                )
            ]

        return [
            StepInstance(
                step_id=step.id,
                instance_id=f"{step.id}-{iteration_index + 1}",
                item=item,
                prompt=self._renderer.render(
                    step.prompt,
                    replace(
                        context,
                        item=ResolvedWorkflowContextValue(
                            present=True,
                            value=item,
                        ),
                    ),
                ),
                iteration_index=iteration_index,
                workflow_instance=step.workflow_instance,
            )
            for iteration_index, item in enumerate(items)
            if f"{step.id}-{iteration_index + 1}"
            not in run_state.completed_instances
            and f"{step.id}-{iteration_index + 1}"
            not in run_state.skipped_instances
        ]
