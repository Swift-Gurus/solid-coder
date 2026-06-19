"""
solid-name: mcp_config_builder
solid-category: utility
solid-tags: [hook]
solid-description: Builds the MCP server JSON configuration string for Claude subprocess sessions from a project root path.
"""

from __future__ import annotations

import sys
from pathlib import Path
_HOOKS_DIR = Path(__file__).resolve().parents[3] / 'hooks'
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

import json
from pathlib import Path


def build_mcp_config(project_root: Path) -> str:
    docs_server = str(project_root / "mcp-server" / "docs" / "server.py")
    pipeline_server = str(project_root / "mcp-server" / "pipeline" / "server.py")
    return json.dumps({
        "mcpServers": {
            "docs": {"command": "python3", "args": [docs_server]},
            "pipeline": {"command": "python3", "args": [pipeline_server]},
        }
    })

