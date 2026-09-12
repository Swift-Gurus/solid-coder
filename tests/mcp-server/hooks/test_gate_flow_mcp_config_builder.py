"""Tests isolated gate-flow MCP configuration."""

import json
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path


ensure_on_path(
    Path(__file__).resolve().parents[3] / "mcp-server",
    Path(__file__).resolve().parent,
)

from json_serializer import JsonSerializer  # noqa: E402
from mcp_config_builder import McpConfigBuilder  # noqa: E402
from mcp_config_profile import McpConfigProfile  # noqa: E402


"""
solid-name: TestGateFlowMcpConfigBuilder
solid-category: unit-test
solid-spec: [SPEC-036]
solid-description: Proves gate child sessions expose only the dedicated flow-engine server.
"""
class TestGateFlowMcpConfigBuilder(unittest.TestCase):
    def test_builds_dedicated_flow_engine_server_only(self) -> None:
        plugin_root = Path("/plugin/root")

        parsed = json.loads(
            McpConfigBuilder(
                project_root=plugin_root,
                profile=McpConfigProfile.GATE_FLOW,
                serializer=JsonSerializer(),
            ).build()
        )

        self.assertEqual(
            list(parsed["mcpServers"]),
            ["solid-coder-flow-engine"],
        )
        server = parsed["mcpServers"]["solid-coder-flow-engine"]
        self.assertEqual(server["command"], "python3")
        self.assertEqual(
            server["args"],
            [str(plugin_root / "mcp-server" / "flow_engine" / "server.py")],
        )


if __name__ == "__main__":
    unittest.main()
