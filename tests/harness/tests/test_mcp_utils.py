"""
solid-name: TestMcpUtils
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for McpConfigBuilder — verifies that the injectable
McpConfigBuilding implementation delegates to the canonical production builder
and produces the same legacy health profile.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE, _PROJECT_ROOT / "hooks", _PROJECT_ROOT / "mcp-server" / "health" / "config")

from json_serializer import JsonSerializer
from mcp_config_builder import McpConfigBuilder as ProductionMcpConfigBuilder
from mcp_config_profile import McpConfigProfile
from mcp_utils import McpConfigBuilder


class TestMcpConfigBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self._builder = McpConfigBuilder()
        self._root = Path("/fake/project")

    def test_build_delegates_to_canonical_production_builder(self):
        expected = ProductionMcpConfigBuilder(
            project_root=self._root,
            profile=McpConfigProfile.LEGACY_HEALTH,
            serializer=JsonSerializer(),
        ).build()
        self.assertEqual(self._builder.build(self._root), expected)


if __name__ == "__main__":
    unittest.main()
