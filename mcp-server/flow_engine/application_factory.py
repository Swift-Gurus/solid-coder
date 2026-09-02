"""Assembles the dedicated flow-engine MCP application."""

from pathlib import Path

from flow_engine.application import FlowEngineApplication
from mcp_server_factory import MCPServerFactory
from pipeline.flow_result_renderer_creating import FlowResultRendererCreating
from pipeline.flow_run_creating import FlowRunCreating
from pipeline.flow_tool_callables_assembler import FlowToolCallablesAssembler
from pipeline.tool_registry import ToolRegistry


_INSTRUCTIONS = (
    "Run named workflows with flow_start. Complete the single step returned by "
    "flow_start or flow_next, then submit its schema-matching output with flow_next. "
    "Repeat until the response reports completion or failure. Do not inspect other "
    "tools to run a workflow."
)


"""
solid-name: FlowEngineApplicationFactory
solid-category: factory
solid-description: Assembles workflow execution, rendering, registration, and transport capabilities.
"""
class FlowEngineApplicationFactory:

    def __init__(
        self,
        plugin_root: Path,
        flow_run_creator: FlowRunCreating,
        flow_renderer_creator: FlowResultRendererCreating,
    ) -> None:
        self._plugin_root = plugin_root
        self._flow_run_creator = flow_run_creator
        self._flow_renderer_creator = flow_renderer_creator

    def make(self) -> FlowEngineApplication:
        server = MCPServerFactory().build(
            "solid-coder-flow-engine",
            "1.0.0",
            instructions=_INSTRUCTIONS,
        )
        return FlowEngineApplication(
            server=server,
            registry=ToolRegistry(server),
            tool_callables=FlowToolCallablesAssembler(
                flow_run=self._flow_run_creator.create(server),
                result_renderer=self._flow_renderer_creator.create(),
            ),
        )
