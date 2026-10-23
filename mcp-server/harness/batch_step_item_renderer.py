"""Renders one domain-labeled batch item and retry guidance."""

from harness.batch_step_item_rendering import BatchStepItemRendering
from harness.step_result import StepResult

"""
solid-name: BatchStepItemRenderer
solid-category: service
solid-spec: [SPEC-042]
solid-description: Renders a batch step result with any applicable retry guidance.
"""


class BatchStepItemRenderer(BatchStepItemRendering):
    def render(self, step: StepResult) -> str:
        label = step.batch.label if step.batch is not None else ""
        if step.rejection_reason is None:
            return f"- {label}"
        return f"- {label}\n  Rejected: {step.rejection_reason}. Try again."
