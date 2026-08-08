"""
solid-name: StepRenderer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Renders step results into the plain text the calling agent sees.
"""

from __future__ import annotations

from harness.step_formatting import StepFormatting
from harness.step_formatter import StepFormatter
from harness.step_rendering import StepRendering
from harness.step_result import StepResult
from harness.subagent_delegating import SubagentDelegating
from harness.subagent_delegator import SubagentDelegator

_STEP_SEPARATOR = "\n\n---\n\n"


class StepRenderer(StepRendering):

    def __init__(
        self,
        subagent_delegator: SubagentDelegating | None = None,
        step_formatter: StepFormatting | None = None,
    ) -> None:
        self._subagent_delegator = subagent_delegator or SubagentDelegator()
        self._step_formatter = step_formatter or StepFormatter()

    def render_steps(self, steps: list[StepResult]) -> str:
        return _STEP_SEPARATOR.join(self._render_step(step) for step in steps)

    def _render_step(self, step: StepResult) -> str:
        body = self._subagent_delegator.wrap_if_subagent(step.prompt, step.execution)
        return self._step_formatter.format(step.instance_id, body, step.rejection_reason)