"""
solid-name: TestMcpUtils
solid-category: unit-test
solid-spec: [SPEC-014]
solid-description: Unit tests for McpConfigBuilder — verifies that the injectable
McpConfigBuilding implementation delegates to build_mcp_config from hooks/mcp_config_builder
and produces the same output as calling the canonical function directly.
"""

from __future__ import annotations

import unittest
from pathlib import Path

from _path_bootstrap import ensure_on_path

_HERE = Path(__file__).resolve().parent
_PROJECT_ROOT = _HERE.parents[2]
_HARNESS_DIR = _PROJECT_ROOT / "tests" / "harness"

ensure_on_path(_HARNESS_DIR, _HERE, _PROJECT_ROOT / "hooks")

from mcp_config_builder import build_mcp_config
from mcp_utils import McpConfigBuilder


class TestMcpConfigBuilder(unittest.TestCase):
    def setUp(self) -> None:
        self._builder = McpConfigBuilder()
        self._root = Path("/fake/project")

    def test_build_delegates_to_canonical_build_mcp_config(self):
        self.assertEqual(self._builder.build(self._root), build_mcp_config(self._root))


if __name__ == "__main__":
    unittest.main()
