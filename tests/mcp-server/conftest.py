"""Makes production MCP modules and local test support importable."""

import sys
from pathlib import Path

TEST_DIR = Path(__file__).resolve().parent
MCP_DIR = Path(__file__).resolve().parents[2] / "mcp-server"

for directory in (MCP_DIR, TEST_DIR):
    if str(directory) not in sys.path:
        sys.path.insert(0, str(directory))
