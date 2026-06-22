"""
solid-description: Provides utilities to add directories to Python's module search path during test execution.
solid-category: unit-test
"""

import sys
from pathlib import Path

_MCP_DIR = Path(__file__).resolve().parents[2]
_PROJECT_ROOT = _MCP_DIR.parent
_MCP_HEALTH = _MCP_DIR / "health"

for _d in (
    _MCP_DIR,
    _MCP_DIR / "session",
    _MCP_DIR / "gate",
    _MCP_DIR / "patch",
    _MCP_DIR / "output",
    _MCP_DIR / "utils",
    _MCP_HEALTH,
    _MCP_HEALTH / "config",
    _MCP_HEALTH / "llm",
    _MCP_HEALTH / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import ensure_on_path  # noqa: E402, F401  # re-export