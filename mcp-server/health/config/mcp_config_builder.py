"""
solid-name: mcp_config_builder
solid-category: utility
solid-tags: [hook]
solid-description: Builds MCP server configuration for isolated model sessions.
"""

from __future__ import annotations

import sys
from pathlib import Path
_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from json_serializer import JsonSerializing
from mcp_config_profile import McpConfigProfile


"""
solid-name: McpConfigBuilder
solid-category: boundary
solid-spec: [SPEC-014, SPEC-036]
solid-description: Provides the selected MCP capability configuration for an isolated model session.
"""
class McpConfigBuilder:
    def __init__(
        self,
        project_root: Path,
        profile: McpConfigProfile,
        serializer: JsonSerializing,
    ) -> None:
        self._project_root = project_root
        self._profile = profile
        self._serializer = serializer

    def build(self) -> str:
        if self._profile is McpConfigProfile.GATE_FLOW:
            servers = {
                "solid-coder-flow-engine": {
                    "command": "python3",
                    "args": [
                        str(
                            self._project_root
                            / "mcp-server"
                            / "flow_engine"
                            / "server.py"
                        )
                    ],
                }
            }
        else:
            servers = {
                "docs": {
                    "command": "python3",
                    "args": [
                        str(self._project_root / "mcp-server" / "docs" / "server.py")
                    ],
                },
                "pipeline": {
                    "command": "python3",
                    "args": [
                        str(
                            self._project_root
                            / "mcp-server"
                            / "pipeline"
                            / "server.py"
                        )
                    ],
                },
            }
        return self._serializer.serialize({"mcpServers": servers})
