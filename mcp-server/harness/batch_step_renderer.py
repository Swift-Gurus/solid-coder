"""Renders a ready batch through its presentation-mode capability."""

from harness.batch_step_rendering_resolving import BatchStepRenderingResolving
from harness.batch_step_rendering import BatchStepRendering
from harness.flow_validation_error import FlowValidationError
from harness.step_result import StepResult


"""
solid-name: BatchStepRenderer
solid-category: service
solid-spec: [SPEC-042, SPEC-043]
solid-description: Renders a ready model-facing batch according to its typed presentation mode.
"""
class BatchStepRenderer(BatchStepRendering):
    def __init__(self, renderers: BatchStepRenderingResolving) -> None:
        self._renderers = renderers

    def render(self, steps: list[StepResult]) -> str:
        if not steps:
            return ""
        presentation = steps[0].batch
        if presentation is None:
            raise FlowValidationError(
                "Batch rendering requires a batch presentation"
            )
        return self._renderers.resolve(presentation.mode).render(steps)
