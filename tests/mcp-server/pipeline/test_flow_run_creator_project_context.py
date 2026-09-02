"""Verifies production flow composition shares one request-scoped project root."""

import sys
import unittest
from pathlib import Path
from unittest.mock import patch


_REPOSITORY_ROOT = Path(__file__).resolve().parents[3]
_MCP_SERVER_DIRECTORY = _REPOSITORY_ROOT / "mcp-server"
_HEALTH_CONFIG_DIRECTORY = _MCP_SERVER_DIRECTORY / "health" / "config"
for _directory in (_MCP_SERVER_DIRECTORY, _HEALTH_CONFIG_DIRECTORY):
    if str(_directory) not in sys.path:
        sys.path.insert(0, str(_directory))

from flow_engine_config import FlowEngineConfig  # noqa: E402
from pipeline.flow_run_creator import FlowRunCreator  # noqa: E402
from solid_coder_config import SolidCoderConfig  # noqa: E402


"""
solid-name: TestFlowRunCreatorProjectContext
solid-category: unit-test
solid-description: Proves production flow storage, workflow discovery, and source operations share request-scoped project context.
"""
class TestFlowRunCreatorProjectContext(unittest.TestCase):

    def test_shares_request_project_reader_across_flow_dependencies(self) -> None:
        config = SolidCoderConfig(flow_engine=FlowEngineConfig())
        transport = object()
        with (
            patch("pipeline.flow_run_creator.FlowRunOrchestratorFactory") as factory,
            patch(
                "pipeline.flow_run_creator.McpRequestContextProjectDirectoryReader",
                create=True,
            ) as project_reader_type,
            patch(
                "pipeline.flow_run_creator.SessionProjectContextPathResolver",
                create=True,
            ) as context_path_type,
            patch(
                "pipeline.flow_run_creator.SessionProjectDirectoryReader",
                create=True,
            ) as session_project_reader_type,
            patch(
                "pipeline.flow_run_creator.SourceOperationRegistrationsFactory"
            ) as source_operations,
        ):
            FlowRunCreator(
                plugin_root=Path("/plugin"),
                config_loader=lambda: config,
            ).create(transport)

        context_path_type.assert_called_once_with()
        session_project_reader_type.assert_called_once_with(
            context_path_type.return_value.resolve
        )
        project_reader_type.assert_called_once()
        project_directory = project_reader_type.return_value.read
        self.assertIs(factory.call_args.kwargs["project_directory"], project_directory)
        source_operations.assert_called_once_with(
            project_directory=project_directory
        )


if __name__ == "__main__":
    unittest.main()
