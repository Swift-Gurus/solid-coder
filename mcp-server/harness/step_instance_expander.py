"""
Expands ready workflow declarations into executable instances.

solid-name: StepInstanceExpander
solid-category: service
solid-spec: [SPEC-010, SPEC-030, SPEC-037]
solid-description: Coordinates ordered workflow iteration expansion while excluding terminal instances.
"""

from __future__ import annotations

from harness.for_each_items_resolving import ForEachItemsResolving
from harness.models import RunState, StepDef, StepInstance, StepOutputs
from harness.step_instance_building import StepInstanceBuilding
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
        instance_builder: StepInstanceBuilding,
    ) -> None:
        self._items_resolver = items_resolver
        self._instance_builder = instance_builder

    def expand(
        self,
        step: StepDef,
        context: WorkflowRunContext,
        run_state: RunState,
    ) -> list[StepInstance]:
        if step.for_each is None:
            item = (
                step.workflow_instance.source_item
                if step.workflow_instance is not None
                else None
            )
            return [
                self._instance_builder.build(
                    step,
                    context,
                    item,
                    f"{step.id}-1",
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
            self._instance_builder.build(
                step,
                context,
                item,
                f"{step.id}-{iteration_index + 1}",
                iteration_index,
            )
            for iteration_index, item in enumerate(items)
            if f"{step.id}-{iteration_index + 1}"
            not in run_state.completed_instances
            and f"{step.id}-{iteration_index + 1}"
            not in run_state.skipped_instances
        ]
