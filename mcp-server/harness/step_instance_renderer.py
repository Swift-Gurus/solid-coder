"""Renders executable workflow-step instances."""

from __future__ import annotations

from typing import Any

from harness.interpolator import TemplateRendering
from harness.models import StepDef, StepInstance
from harness.step_instance_rendering import StepInstanceRendering


"""
solid-name: StepInstanceRenderer
solid-category: service
solid-spec: [SPEC-010, SPEC-030]
solid-description: Renders standard and iterated workflow declarations into executable step instances.
"""
class StepInstanceRenderer(StepInstanceRendering):
    def __init__(self, renderer: TemplateRendering) -> None:
        self._renderer = renderer

    def render_standard(
        self,
        step: StepDef,
        context: dict[str, Any],
    ) -> StepInstance:
        return StepInstance(
            step_id=step.id,
            instance_id=f"{step.id}-1",
            item=None,
            prompt=self._renderer.render(step.prompt, context),
        )

    def render_iteration(
        self,
        step: StepDef,
        context: dict[str, Any],
        item: Any,
        iteration_index: int,
    ) -> StepInstance:
        return StepInstance(
            step_id=step.id,
            instance_id=f"{step.id}-{iteration_index + 1}",
            item=item,
            prompt=self._renderer.render(step.prompt, {**context, "item": item}),
            iteration_index=iteration_index,
        )
