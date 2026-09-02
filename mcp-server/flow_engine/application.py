"""Runs the model-facing flow-engine MCP application."""

from common.mcp_meta import COMPLETE_FLOW_OUTPUT
from message_transport_running import MessageTransportRunning
from pipeline.tool_callables_building import ToolCallablesBuilding
from tool_registering import ToolRegistering


"""
solid-name: FlowEngineApplication
solid-category: service
solid-description: Exposes workflow progression tools through an MCP message transport.
"""
class FlowEngineApplication:

    def __init__(
        self,
        server: MessageTransportRunning,
        registry: ToolRegistering,
        tool_callables: ToolCallablesBuilding,
    ) -> None:
        self._server = server
        self._registry = registry
        self._tool_callables = tool_callables

    def run(self) -> None:
        self._register_tools()
        self._server.run()

    def _register_tools(self) -> None:
        callables = self._tool_callables.build()
        self._registry.register(
            "flow_start",
            "Start a named workflow and return its first ready step. Continue it with flow_next.",
            {
                "type": "object",
                "properties": {
                    "flow": {
                        "type": "string",
                        "description": "Workflow ID or explicit workflow YAML path.",
                    },
                    "params": {
                        "type": "object",
                        "description": "Workflow inputs referenced as params by its steps.",
                    },
                    "isolated": {
                        "type": "boolean",
                        "description": "Use only when a workflow instruction requests an isolated child run.",
                    },
                },
                "required": ["flow"],
            },
            callables["flow_start"],
            meta=COMPLETE_FLOW_OUTPUT,
        )
        self._registry.register(
            "flow_next",
            "Submit the current step output and return the next ready step or terminal result.",
            {
                "type": "object",
                "properties": {
                    "outputs": {
                        "type": "object",
                        "description": "Current output keyed by the instance ID returned by the flow.",
                    },
                    "run_id": {
                        "type": "string",
                        "description": "Run ID returned when flow_start created an isolated run.",
                    },
                },
            },
            callables["flow_next"],
            meta=COMPLETE_FLOW_OUTPUT,
        )
