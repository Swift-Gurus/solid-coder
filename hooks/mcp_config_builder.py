"""
solid-name: mcp_config_builder
solid-category: utility
solid-tags: [hook]
solid-description: Builds the standard docs+pipeline MCP server JSON config string for
Claude subprocess sessions. Accepts a project root path and constructs server paths
for mcp-server/server.py and mcp-server/pipeline/server.py. Canonical implementation
shared by both the pre-write gate hook and the principle test harness.
"""

from __future__ import annotations

import json
from pathlib import Path


def build_mcp_config(project_root: Path) -> str:
    docs_server = str(project_root / "mcp-server" / "server.py")
    pipeline_server = str(project_root / "mcp-server" / "pipeline" / "server.py")
    return json.dumps({
        "mcpServers": {
            "docs": {"command": "python3", "args": [docs_server]},
            "pipeline": {"command": "python3", "args": [pipeline_server]},
        }
    })
