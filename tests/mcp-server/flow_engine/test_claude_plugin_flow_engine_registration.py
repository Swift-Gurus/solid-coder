"""Verifies that the Claude plugin exposes the shipped flow-engine server."""

import json
import unittest
from pathlib import Path


_PROJECT_ROOT = Path(__file__).resolve().parents[3]


"""
solid-name: TestClaudePluginFlowEngineRegistration
solid-category: unit-test
solid-spec: [SPEC-039]
solid-description: Prevents Claude plugin packaging from omitting the flow-engine MCP server used by production review workflows.
"""
class TestClaudePluginFlowEngineRegistration(unittest.TestCase):

    def test_manifest_registers_checkout_flow_engine_server(self) -> None:
        manifest = json.loads(
            (_PROJECT_ROOT / ".claude-plugin" / "plugin.json").read_text(
                encoding="utf-8"
            )
        )

        registration = manifest["mcpServers"]["flow-engine"]
        self.assertEqual(registration["command"], "python3")
        self.assertEqual(
            registration["args"],
            ["${CLAUDE_PLUGIN_ROOT}/mcp-server/flow_engine/server.py"],
        )


if __name__ == "__main__":
    unittest.main()
