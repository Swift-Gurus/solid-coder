"""Creates production flow-run orchestration services."""

from pathlib import Path
from typing import Callable

from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.mcp_request_context_session_reader import McpRequestContextSessionReader
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from hc_config_schema import load_config
from hook_utils import _resolve_project_root
from message_transport_running import MessageTransportRunning
from pipeline.flow_run_creating import FlowRunCreating
from solid_coder_config import SolidCoderConfig
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)


ConfigLoading = Callable[[], SolidCoderConfig]


"""
solid-name: FlowRunCreator
solid-category: service
solid-description: Creates production flow-run orchestration.
"""
class FlowRunCreator(FlowRunCreating):
    def __init__(
        self,
        plugin_root: Path,
        config_loader: ConfigLoading = load_config,
    ) -> None:
        self._plugin_root = plugin_root
        self._config_loader = config_loader

    def create(self, transport: MessageTransportRunning) -> FlowRunOrchestrating:
        flow_engine_config = self._config_loader().flow_engine
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(),
            plugin_root=self._plugin_root,
            session_reader=McpRequestContextSessionReader(
                call_meta_provider=transport
            ),
            session_delegate_max_workers=(
                flow_engine_config.max_parallel_sessions
            ),
            operation_registrations=SourceOperationRegistrationsFactory(
                project_directory=_resolve_project_root,
            ).make(),
        ).build()
