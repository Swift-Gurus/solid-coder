"""
solid-description: Verifies that MCP server configuration is correctly generated for a given project root.
solid-category: unit-test
"""

from __future__ import annotations

import json
import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

ensure_on_path(Path(__file__).resolve().parents[1], Path(__file__).resolve().parent)

from mcp_config_builder import build_mcp_config


class TestBuildMcpConfig(unittest.TestCase):
    def setUp(self) -> None:
        self._root = Path("/fake/project")
        self._parsed = json.loads(build_mcp_config(self._root))

    def test_returns_valid_json(self):
        result = build_mcp_config(self._root)
        json.loads(result)

    def test_includes_docs_server(self):
        self.assertIn("docs", self._parsed["mcpServers"])

    def test_includes_pipeline_server(self):
        self.assertIn("pipeline", self._parsed["mcpServers"])

    def test_docs_server_path_derived_from_project_root(self):
        expected = str(self._root / "mcp-server" / "server.py")
        self.assertIn(expected, self._parsed["mcpServers"]["docs"]["args"])

    def test_pipeline_server_path_derived_from_project_root(self):
        expected = str(self._root / "mcp-server" / "pipeline" / "server.py")
        self.assertIn(expected, self._parsed["mcpServers"]["pipeline"]["args"])

    def test_both_servers_use_python3_command(self):
        self.assertEqual(self._parsed["mcpServers"]["docs"]["command"], "python3")
        self.assertEqual(self._parsed["mcpServers"]["pipeline"]["command"], "python3")

    def test_different_roots_produce_different_paths(self):
        root_a = Path("/proj/a")
        root_b = Path("/proj/b")
        self.assertNotEqual(build_mcp_config(root_a), build_mcp_config(root_b))


if __name__ == "__main__":
    unittest.main()
