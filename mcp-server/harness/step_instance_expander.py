"""Expands ready workflow declarations into executable instances."""

from __future__ import annotations

from typing import Any

from harness.empty_step_instance_rendering import EmptyStepInstanceRendering
from harness.for_each_items_resolving import ForEachItemsResolving
from harness.models import RunState, StepDef, StepInstance
from harness.step_instance_expanding import StepInstanceExpanding
from harness.step_instance_rendering import StepInstanceRendering


"""
solid-name: StepInstanceExpander
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Coordinates ordered workflow iteration expansion while excluding completed instances.
"""
class StepInstanceExpander(StepInstanceExpanding):
    def __init__(
        self,
        items_resolver: ForEachItemsResolving,
        instance_renderer: StepInstanceRendering,
        empty_instance_renderer: EmptyStepInstanceRendering,
    ) -> None:
        self._items_resolver = items_resolver
        self._instance_renderer = instance_renderer
        self._empty_instance_renderer = empty_instance_renderer

    def expand(
        self,
        step: StepDef,
        context: dict[str, Any],
        run_state: RunState,
    ) -> list[StepInstance]:
        if step.for_each is None:
            return [self._instance_renderer.render_standard(step, context)]

        items = self._items_resolver.resolve(
            step.id,
            step.for_each,
            context,
        )
        if not items:
            return [self._empty_instance_renderer.render(step)]

        return [
            self._instance_renderer.render_iteration(
                step,
                context,
                item,
                iteration_index,
            )
            for iteration_index, item in enumerate(items)
            if f"{step.id}-{iteration_index + 1}"
            not in run_state.completed_instances
        ]
