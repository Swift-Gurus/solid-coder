"""Renders one domain-labeled batch item and retry guidance."""

from harness.batch_step_item_rendering import BatchStepItemRendering
from harness.step_result import StepResult


"""
solid-name: BatchStepItemRenderer
solid-category: service
solid-spec: [SPEC-042]
solid-description: Formats one batch item using its domain label and optional rejection reason.
"""
class BatchStepItemRenderer(BatchStepItemRendering):
    def render(self, step: StepResult) -> str:
        label = step.batch.label if step.batch is not None else ""
        if step.rejection_reason is None:
            return f"- {label}"
        return (
            f"- {label}\n"
            f"  Rejected: {step.rejection_reason}. Try again."
        )
