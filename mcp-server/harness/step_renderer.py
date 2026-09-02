from __future__ import annotations

from harness.batch_step_rendering import BatchStepRendering
from harness.ready_step_selecting import ReadyStepSelecting
from harness.sibling_batch_step_selecting import SiblingBatchStepSelecting
from harness.single_step_rendering import SingleStepRendering
from harness.step_rendering import StepRendering
from harness.step_result import StepResult


"""
solid-name: StepRenderer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Delegates next-step selection and rendering for model-facing flow results.
"""
class StepRenderer(StepRendering):

    def __init__(
        self,
        ready_step_selector: ReadyStepSelecting,
        sibling_batch_selector: SiblingBatchStepSelecting,
        single_step_renderer: SingleStepRendering,
        batch_step_renderer: BatchStepRendering,
    ) -> None:
        self._ready_step_selector = ready_step_selector
        self._sibling_batch_selector = sibling_batch_selector
        self._single_step_renderer = single_step_renderer
        self._batch_step_renderer = batch_step_renderer

    def render_steps(self, steps: list[StepResult]) -> str:
        selected = self._ready_step_selector.select(steps)
        if selected is None:
            return ""
        if selected.batch is None:
            return self._single_step_renderer.render(selected)
        siblings = self._sibling_batch_selector.select(selected, steps)
        return self._batch_step_renderer.render(siblings)
