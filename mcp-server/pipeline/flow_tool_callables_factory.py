"""Builds the callable map exposed by flow MCP tools."""

from typing import Optional

from harness.flow_result_rendering import FlowResultRendering
from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.flow_status_rendering import FlowStatusRendering
from pipeline.tool_callables_building import ToolCallablesBuilding


"""
solid-name: FlowToolCallablesFactory
solid-category: factory
solid-spec: [SPEC-031]
solid-description: Builds model-facing flow callables from execution and rendering capabilities.
"""
class FlowToolCallablesFactory(ToolCallablesBuilding):
    def __init__(
        self,
        flow_run: FlowRunOrchestrating,
        result_renderer: FlowResultRendering,
        status_renderer: FlowStatusRendering,
    ) -> None:
        self._flow_run = flow_run
        self._result_renderer = result_renderer
        self._status_renderer = status_renderer

    def build(self) -> dict:
        return {
            "flow_start": self._flow_start,
            "flow_next": self._flow_next,
            "flow_status": self._flow_status,
            "flow_clear_lock": self._flow_clear_lock,
        }

    def _flow_start(
        self,
        flow: str,
        params: Optional[dict] = None,
        isolated: bool = False,
    ) -> str:
        return self._result_renderer.render_start(
            self._flow_run.flow_start(flow, params, isolated)
        )

    def _flow_next(
        self,
        outputs: Optional[dict] = None,
        run_id: Optional[str] = None,
    ) -> str:
        return self._result_renderer.render_next(
            self._flow_run.flow_next(outputs, run_id)
        )

    def _flow_status(self, run_id: Optional[str] = None) -> dict:
        return self._status_renderer.render(self._flow_run.flow_status(run_id))

    def _flow_clear_lock(self, run_id: str) -> str:
        return self._flow_run.flow_clear_lock(run_id)
