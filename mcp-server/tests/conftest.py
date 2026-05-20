"""Pytest configuration — add mcp-server/ to sys.path so test modules can import
from the sibling `tests.helpers` package and from `lib.*` utilities."""

import sys
from pathlib import Path

MCP_DIR = Path(__file__).resolve().parents[1]
if str(MCP_DIR) not in sys.path:
    sys.path.insert(0, str(MCP_DIR))
