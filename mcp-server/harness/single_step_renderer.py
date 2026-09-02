"""Formats one selected workflow step for model consumption."""

from harness.single_step_rendering import SingleStepRendering
from harness.step_formatting import StepFormatting
from harness.step_result import StepResult
from harness.subagent_delegating import SubagentDelegating


"""
solid-name: SingleStepRenderer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Formats one selected step after applying its configured delegation instruction.
"""
class SingleStepRenderer(SingleStepRendering):
    def __init__(
        self,
        subagent_delegator: SubagentDelegating,
        step_formatter: StepFormatting,
    ) -> None:
        self._subagent_delegator = subagent_delegator
        self._step_formatter = step_formatter

    def render(self, step: StepResult) -> str:
        body = self._subagent_delegator.wrap_if_subagent(
            step.prompt,
            step.execution,
        )
        return self._step_formatter.format(
            step.instance_id,
            body,
            step.rejection_reason,
        )
