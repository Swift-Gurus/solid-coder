"""Creates production flow-run orchestration services."""

from pathlib import Path

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.mcp_request_context_session_reader import McpRequestContextSessionReader
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from message_transport_running import MessageTransportRunning
from pipeline.flow_run_creating import FlowRunCreating


"""
solid-name: FlowRunCreator
solid-category: service
solid-description: Creates production flow-run orchestration.
"""
class FlowRunCreator(FlowRunCreating):
    def __init__(self, plugin_root: Path) -> None:
        self._plugin_root = plugin_root

    def create(self, transport: MessageTransportRunning) -> FlowRunOrchestrating:
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(),
            plugin_root=self._plugin_root,
            session_reader=McpRequestContextSessionReader(
                call_meta_provider=transport
            ),
        ).build()
