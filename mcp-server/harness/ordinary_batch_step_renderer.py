"""Renders one shared instruction for an ordinary sibling batch."""

from harness.batch_step_item_rendering import BatchStepItemRendering
from harness.batch_step_rendering import BatchStepRendering
from harness.step_result import StepResult


"""
solid-name: OrdinaryBatchStepRenderer
solid-category: service
solid-spec: [SPEC-042]
solid-description: Renders one shared prompt and domain-labelled item list for an ordinary model-facing batch.
"""
class OrdinaryBatchStepRenderer(BatchStepRendering):
    def __init__(self, item_renderer: BatchStepItemRendering) -> None:
        self._item_renderer = item_renderer

    def render(self, steps: list[StepResult]) -> str:
        if not steps:
            return ""
        items = [
            self._item_renderer.render(step)
            for step in steps
            if step.batch is not None
        ]
        rendered_items = "\n".join(items)
        return (
            f"{steps[0].prompt}\n\n"
            "Apply this instruction to every item below:\n"
            f"{rendered_items}\n\n"
            "Call flow_next with outputs as one object keyed exactly by these "
            "item labels. Each value must match this step's declared outputs."
        )
