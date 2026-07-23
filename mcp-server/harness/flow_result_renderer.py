"""
solid-name: FlowResultRenderer
solid-category: service
solid-spec: [SPEC-013]
solid-description: Renders flow execution results as plain text for agent consumption.
"""

from __future__ import annotations

from harness.flow_next_result import FlowNextResult
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_start_result import FlowStartResult
from harness.step_result import StepResult

_SUBAGENT_MODE = "subagent"
_STEP_SEPARATOR = "\n\n---\n\n"
_TERMINAL_MESSAGES = {
    "done": "Flow complete.",
    "failed": "Flow failed — a step exhausted its retry attempts.",
    "timed_out": "Flow timed out — reached the flow's max_turns limit.",
}


class FlowResultRenderer(FlowResultRendering):

    def render_start(self, result: FlowStartResult) -> str:
        if result.error:
            return result.error
        return self._render_steps(result.steps)

    def render_next(self, result: FlowNextResult) -> str:
        if result.error:
            return result.error
        terminal_message = _TERMINAL_MESSAGES.get(result.status)
        if terminal_message is not None:
            return terminal_message
        return self._render_steps(result.steps)

    def _render_steps(self, steps: list[StepResult]) -> str:
        return _STEP_SEPARATOR.join(self._render_step(step) for step in steps)

    def _render_step(self, step: StepResult) -> str:
        body = step.prompt
        if step.execution.get("mode") == _SUBAGENT_MODE:
            body = f"Launch a subagent with the following prompt:\n\n{body}"

        header = f"id: {step.instance_id}"
        if step.rejection_reason is not None:
            header = (
                f"{header}\nRejected: {step.rejection_reason}. Try again — "
                f"you have {step.attempts_remaining} attempt(s) left."
            )
        return f"{header}\n\n{body}"
