"""Selects the run's presentation contract without changing ready-work scope."""

from harness.batch_step_rendering import BatchStepRendering
from harness.ready_step_selecting import ReadyStepSelecting
from harness.sibling_batch_step_selecting import SiblingBatchStepSelecting
from harness.step_rendering import StepRendering
from harness.step_result import StepResult

"""
solid-name: SubmissionFormatStepRenderer
solid-category: service
solid-spec: [SPEC-068]
solid-description: Routes persisted flat assignments or unchanged nested steps through the selected presentation capability.
"""


class SubmissionFormatStepRenderer(StepRendering):
    def __init__(
        self,
        nested_renderer: StepRendering,
        flat_renderer: BatchStepRendering,
        ready_selector: ReadyStepSelecting,
        sibling_selector: SiblingBatchStepSelecting,
    ) -> None:
        self._nested_renderer = nested_renderer
        self._flat_renderer = flat_renderer
        self._ready_selector = ready_selector
        self._sibling_selector = sibling_selector

    def render_steps(self, steps: list[StepResult]) -> str:
        selected = self._ready_selector.select(steps)
        if selected is None or selected.submission_id is None:
            return self._nested_renderer.render_steps(steps)
        return self._flat_renderer.render(
            self._sibling_selector.select(selected, steps)
        )
