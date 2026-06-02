"""
solid-name: mcp_utils
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Shared MCP server configuration utilities for the principle test harness.
Provides McpConfigBuilder, the injectable implementation of McpConfigBuilding, and the
build_mcp_config convenience function. Delegates MCP config construction to mcp_config_builder
in hooks/, which owns the canonical implementation.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HARNESS_DIR.parents[1] / "hooks"
for _d in (str(_HARNESS_DIR), str(_HOOKS_DIR)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from interfaces import McpConfigBuilding  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402


class McpConfigBuilder(McpConfigBuilding):
    def build(self, project_root: Path) -> str:
        return build_mcp_config(project_root)
