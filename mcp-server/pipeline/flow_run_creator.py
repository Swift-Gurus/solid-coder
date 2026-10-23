"""Creates production flow-run orchestration services."""

from pathlib import Path

from harness.flow_run_orchestrating import FlowRunOrchestrating
from harness.flow_run_orchestrator_factory import FlowRunOrchestratorFactory
from harness.mcp_request_context_session_reader import McpRequestContextSessionReader
from harness.project_context import (
    McpRequestContextProjectDirectoryReader,
)
from harness.runs_base_dir_resolver import RunsBaseDirResolver
from health.config.solid_coder_config_loader import SolidCoderConfigLoading
from hook_utils import solid_coder_project_dir
from message_transport_running import MessageTransportRunning
from pipeline.flow_run_creating import FlowRunCreating
from review.review_operation_registrations_factory import (
    ReviewOperationRegistrationsFactory,
)
from session.project_context import (
    DEFAULT_SESSION_ROOT,
    SessionProjectContextPathResolver,
    SessionProjectDirectoryReader,
)
from source.source_operation_registrations_factory import (
    SourceOperationRegistrationsFactory,
)

"""
solid-name: FlowRunCreator
solid-category: service
solid-description: Creates production flow-run orchestration.
"""


class FlowRunCreator(FlowRunCreating):
    def __init__(
        self,
        plugin_root: Path,
        config_loader: SolidCoderConfigLoading,
    ) -> None:
        self._plugin_root = plugin_root
        self._config_loader = config_loader

    def create(self, transport: MessageTransportRunning) -> FlowRunOrchestrating:
        config = self._config_loader.load()
        flow_engine_config = config.flow_engine
        session_reader = McpRequestContextSessionReader(call_meta_provider=transport)
        project_directory_reader = McpRequestContextProjectDirectoryReader(
            session_reader=session_reader,
            session_project_directory=SessionProjectDirectoryReader(
                SessionProjectContextPathResolver(root_directory=DEFAULT_SESSION_ROOT)
            ),
        )
        return FlowRunOrchestratorFactory(
            base_dir_resolver=RunsBaseDirResolver(
                project_dir_fn=lambda: solid_coder_project_dir(
                    project_directory_reader.read()
                )
            ),
            plugin_root=self._plugin_root,
            submission_format=config.feature_flags.flow_submission_format,
            project_directory=project_directory_reader,
            session_reader=session_reader,
            session_delegate_max_workers=(flow_engine_config.max_parallel_sessions),
            operation_registrations=[
                *SourceOperationRegistrationsFactory(
                    project_directory=project_directory_reader,
                ).make(),
                *ReviewOperationRegistrationsFactory().make(),
            ],
        ).build()
