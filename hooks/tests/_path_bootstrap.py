"""
solid-description: Re-exports ensure_on_path from the canonical hook_utils definition for use in hook test suites.
solid-category: unit-test
"""

import sys
from pathlib import Path

_HOOKS_DIR = Path(__file__).resolve().parents[1]
_PROJECT_ROOT = _HOOKS_DIR.parent
_MCP_HEALTH = _PROJECT_ROOT / "mcp-server" / "health"

for _d in (
    _HOOKS_DIR,
    _HOOKS_DIR / "session",
    _HOOKS_DIR / "gate",
    _HOOKS_DIR / "patch",
    _HOOKS_DIR / "output",
    _HOOKS_DIR / "utils",
    _MCP_HEALTH,
    _MCP_HEALTH / "config",
    _MCP_HEALTH / "llm",
    _MCP_HEALTH / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import ensure_on_path  # noqa: E402, F401  # re-export
