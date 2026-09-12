"""
solid-name: mcp_utils
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Shared MCP server configuration utilities for the principle test harness.
Provides the injectable McpConfigBuilding adapter and delegates to the canonical
production builder object.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _HARNESS_DIR.parents[1]
_HOOKS_DIR = _PROJECT_ROOT / "hooks"
_MCP_HEALTH_CONFIG = _PROJECT_ROOT / "mcp-server" / "health" / "config"
for _d in (str(_HARNESS_DIR), str(_HOOKS_DIR), str(_MCP_HEALTH_CONFIG)):
    if _d not in sys.path:
        sys.path.insert(0, _d)

from interfaces import McpConfigBuilding  # noqa: E402
from json_serializer import JsonSerializer  # noqa: E402
from mcp_config_builder import McpConfigBuilder as ProductionMcpConfigBuilder  # noqa: E402
from mcp_config_profile import McpConfigProfile  # noqa: E402


class McpConfigBuilder(McpConfigBuilding):
    def build(self, project_root: Path) -> str:
        return ProductionMcpConfigBuilder(
            project_root=project_root,
            profile=McpConfigProfile.LEGACY_HEALTH,
            serializer=JsonSerializer(),
        ).build()
