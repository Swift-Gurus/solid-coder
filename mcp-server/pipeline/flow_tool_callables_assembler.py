"""Assembles model-facing flow tool callables."""

from harness.flow_result_rendering import FlowResultRendering
from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.flow_status_response_renderer import FlowStatusResponseRenderer
from pipeline.flow_tool_callables_factory import FlowToolCallablesFactory
from pipeline.tool_callables_building import ToolCallablesBuilding


"""
solid-name: FlowToolCallablesAssembler
solid-category: factory
solid-spec: [SPEC-031]
solid-description: Assembles flow execution and rendering capabilities into model-facing callables.
"""
class FlowToolCallablesAssembler(ToolCallablesBuilding):
    def __init__(
        self,
        flow_run: FlowRunOrchestrating,
        result_renderer: FlowResultRendering,
    ) -> None:
        self._callables = FlowToolCallablesFactory(
            flow_run=flow_run,
            result_renderer=result_renderer,
            status_renderer=FlowStatusResponseRenderer(),
        )

    def build(self) -> dict:
        return self._callables.build()
