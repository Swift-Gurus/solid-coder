"""
solid-description: Verifies that MCP server configuration is correctly generated for a given project root.
solid-category: unit-test
"""

from __future__ import annotations

import json
import sys
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[3] / "mcp-server" / "hooks", Path(__file__).resolve().parent)

from json_serializer import JsonSerializer
from mcp_config_builder import McpConfigBuilder
from mcp_config_profile import McpConfigProfile


class TestBuildMcpConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._root = Path("/fake/project")
        self._builder = McpConfigBuilder(
            project_root=self._root,
            profile=McpConfigProfile.LEGACY_HEALTH,
            serializer=JsonSerializer(),
        )
        self._parsed = json.loads(self._builder.build())

    def test_returns_valid_json(self):
        result = self._builder.build()
        json.loads(result)

    def test_includes_docs_server(self):
        self.assertIn("docs", self._parsed["mcpServers"])

    def test_includes_pipeline_server(self):
        self.assertIn("pipeline", self._parsed["mcpServers"])

    def test_docs_server_path_derived_from_project_root(self):
        expected = str(self._root / "mcp-server" / "docs" / "server.py")
        self.assertIn(expected, self._parsed["mcpServers"]["docs"]["args"])

    def test_pipeline_server_path_derived_from_project_root(self):
        expected = str(self._root / "mcp-server" / "pipeline" / "server.py")
        self.assertIn(expected, self._parsed["mcpServers"]["pipeline"]["args"])

    def test_both_servers_reuse_parent_interpreter(self):
        self.assertEqual(self._parsed["mcpServers"]["docs"]["command"], sys.executable)
        self.assertEqual(self._parsed["mcpServers"]["pipeline"]["command"], sys.executable)

    def test_supplied_interpreter_is_preserved_without_path_lookup(self):
        executable = "/runtime with spaces/bin/python3.12"
        config = json.loads(McpConfigBuilder(
            self._root, McpConfigProfile.LEGACY_HEALTH, JsonSerializer(),
            executable=executable,
        ).build())

        self.assertEqual(config["mcpServers"]["docs"]["command"], executable)
        self.assertEqual(config["mcpServers"]["pipeline"]["command"], executable)

    def test_different_roots_produce_different_paths(self):
        root_a = Path("/proj/a")
        root_b = Path("/proj/b")
        config_a = McpConfigBuilder(
            root_a,
            McpConfigProfile.LEGACY_HEALTH,
            JsonSerializer(),
        ).build()
        config_b = McpConfigBuilder(
            root_b,
            McpConfigProfile.LEGACY_HEALTH,
            JsonSerializer(),
        ).build()
        self.assertNotEqual(config_a, config_b)


if __name__ == "__main__":
    unittest.main()
