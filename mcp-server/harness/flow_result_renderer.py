from __future__ import annotations

from harness.flow_next_result import FlowNextResult
from harness.flow_result_rendering import FlowResultRendering
from harness.flow_start_result import FlowStartResult
from harness.step_rendering import StepRendering
from harness.terminal_message_resolving import TerminalMessageResolving


"""
solid-name: FlowResultRenderer
solid-category: service
solid-spec: [SPEC-031]
solid-description: Renders flow execution results for agent consumption.
"""
class FlowResultRenderer(FlowResultRendering):

    def __init__(
        self,
        step_renderer: StepRendering,
        terminal_message_resolver: TerminalMessageResolving,
    ) -> None:
        self._step_renderer = step_renderer
        self._terminal_message_resolver = terminal_message_resolver

    def render_start(self, result: FlowStartResult) -> str:
        message = self._terminal_message_resolver.resolve(result.error, result.status)
        if message is not None:
            return message
        body = self._step_renderer.render_steps(result.steps)
        if result.isolated:
            header = f'run_id: {result.run_id}\n\nPass run_id="{result.run_id}" on every flow_next call for this run.'
            return f"{header}\n\n{body}"
        return body

    def render_next(self, result: FlowNextResult) -> str:
        message = self._terminal_message_resolver.resolve(result.error, result.status)
        if message is not None:
            return message
        return self._step_renderer.render_steps(result.steps)
