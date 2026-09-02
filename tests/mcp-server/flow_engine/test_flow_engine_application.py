"""Verifies the model-facing boundary of the flow-engine MCP application."""

import sys
import unittest
from pathlib import Path
from unittest.mock import Mock


_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
if str(_MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER))

from flow_engine.application import FlowEngineApplication  # noqa: E402
from common.mcp_meta import COMPLETE_FLOW_OUTPUT  # noqa: E402


"""
solid-name: TestFlowEngineApplication
solid-category: test
solid-description: Verifies that the flow-engine MCP boundary exposes only workflow progression tools.
"""
class TestFlowEngineApplication(unittest.TestCase):

    def test_registers_only_start_and_next_before_running_transport(self) -> None:
        server = Mock()
        registry = Mock()
        callables = Mock()
        callables.build.return_value = {
            "flow_start": Mock(),
            "flow_next": Mock(),
            "flow_status": Mock(),
            "flow_clear_lock": Mock(),
        }
        application = FlowEngineApplication(
            server=server,
            registry=registry,
            tool_callables=callables,
        )

        application.run()

        self.assertEqual(
            [call.args[0] for call in registry.register.call_args_list],
            ["flow_start", "flow_next"],
        )
        for registration in registry.register.call_args_list:
            self.assertEqual(
                registration.kwargs["meta"],
                COMPLETE_FLOW_OUTPUT,
            )
        server.run.assert_called_once_with()


if __name__ == "__main__":
    unittest.main()
