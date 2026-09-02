"""Verifies assembly of the dedicated flow-engine MCP application."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
if str(_MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER))

from flow_engine.application import FlowEngineApplication  # noqa: E402
from flow_engine.application_factory import FlowEngineApplicationFactory  # noqa: E402


"""
solid-name: TestFlowEngineApplicationFactory
solid-category: test
solid-description: Verifies the dedicated flow-engine server identity and model-facing initialization guidance.
"""
class TestFlowEngineApplicationFactory(unittest.TestCase):

    @patch("flow_engine.application_factory.MCPServerFactory")
    def test_builds_dedicated_server_with_workflow_instructions(
        self,
        server_factory_type: Mock,
    ) -> None:
        server = Mock()
        server_factory_type.return_value.build.return_value = server
        flow_run_creator = Mock()
        flow_run_creator.create.return_value = Mock()
        renderer_creator = Mock()
        renderer_creator.create.return_value = Mock()

        application = FlowEngineApplicationFactory(
            plugin_root=Path("/plugin"),
            flow_run_creator=flow_run_creator,
            flow_renderer_creator=renderer_creator,
        ).make()

        self.assertIsInstance(application, FlowEngineApplication)
        build_call = server_factory_type.return_value.build.call_args
        self.assertEqual(build_call.args, ("solid-coder-flow-engine", "1.0.0"))
        instructions = build_call.kwargs["instructions"]
        self.assertIn("flow_start", instructions)
        self.assertIn("flow_next", instructions)
        self.assertLessEqual(len(instructions), 512)
        flow_run_creator.create.assert_called_once_with(server)


if __name__ == "__main__":
    unittest.main()
