"""
solid-name: FlowResultRenderer
solid-category: service
solid-spec: [SPEC-013]
solid-description: Renders flow execution results for agent consumption.
"""

from __future__ import annotations

from harness.delegate_instruction_builder import DelegateInstructionBuilder
from harness.delegate_instruction_building import DelegateInstructionBuilding
from harness.flow_next_result import FlowNextResult
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_start_result import FlowStartResult
from harness.step_result import StepResult

_SUBAGENT_MODE = "subagent"
_STEP_SEPARATOR = "\n\n---\n\n"
_TERMINAL_MESSAGES = {
    "done": "Flow complete.",
}


class FlowResultRenderer(FlowResultRendering):

    def __init__(self, delegate_instruction_builder: DelegateInstructionBuilding | None = None) -> None:
        self._delegate_instruction_builder = delegate_instruction_builder or DelegateInstructionBuilder()

    def render_start(self, result: FlowStartResult) -> str:
        if result.error:
            return result.error
        body = self._render_steps(result.steps)
        if result.isolated:
            header = f'run_id: {result.run_id}\n\nPass run_id="{result.run_id}" on every flow_next/flow_status call for this run.'
            return f"{header}\n\n{body}"
        return body

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
            instruction = self._delegate_instruction_builder.build(body)
            body = f"Launch a subagent with the following prompt:\n\n{instruction}"

        header = f"id: {step.instance_id}"
        if step.rejection_reason is not None:
            header = f"{header}\nRejected: {step.rejection_reason}. Try again."
        return f"{header}\n\n{body}"