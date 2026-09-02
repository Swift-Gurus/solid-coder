"""Verifies that workflow progression is not exposed by the legacy pipeline MCP server."""

import sys
import unittest
from collections import defaultdict
from pathlib import Path
from unittest.mock import Mock


_MCP_SERVER = Path(__file__).resolve().parents[3] / "mcp-server"
if str(_MCP_SERVER) not in sys.path:
    sys.path.insert(0, str(_MCP_SERVER))

from pipeline.server import ApplicationBootstrapper  # noqa: E402


"""
solid-name: TestPipelineFlowBoundary
solid-category: test
solid-description: Verifies that the legacy pipeline endpoint does not expose workflow progression tools.
"""
class TestPipelineFlowBoundary(unittest.TestCase):

    def test_does_not_register_flow_tools(self) -> None:
        registry = Mock()
        pipeline_callables = Mock()
        pipeline_callables.build.return_value = defaultdict(Mock)
        flow_callables = Mock()
        flow_callables.build.return_value = {
            "flow_start": Mock(),
            "flow_next": Mock(),
        }
        application = ApplicationBootstrapper(
            server=Mock(),
            registry=registry,
            tool_callables=pipeline_callables,
            flow_callables=flow_callables,
        )

        application.run()

        registered_names = [
            call.args[0]
            for call in registry.register.call_args_list
        ]
        self.assertNotIn("flow_start", registered_names)
        self.assertNotIn("flow_next", registered_names)


if __name__ == "__main__":
    unittest.main()
