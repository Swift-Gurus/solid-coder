"""Renders one shared instruction for a ready batch of domain-labeled items."""

from harness.batch_step_rendering import BatchStepRendering
from harness.batch_step_item_rendering import BatchStepItemRendering
from harness.step_result import StepResult


"""
solid-name: BatchStepRenderer
solid-category: service
solid-spec: [SPEC-042]
solid-description: Renders a validated shared step prompt once with only the domain labels required for keyed batch submission.
"""
class BatchStepRenderer(BatchStepRendering):
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
