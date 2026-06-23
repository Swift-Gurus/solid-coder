"""
solid-description: Validates source code against language-specific health check rules.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
from typing import Optional

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from hook_utils import PLUGIN_ROOT  # noqa: E402
from hc_checker_factory import make_health_checker  # noqa: E402
from hc_runner_factory import select_strategy  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402

SUPPORTED_EXTENSIONS: dict = {
    ".swift": "Swift",
    ".py": "Python",
}


def _check(content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
    strategy = select_strategy()
    strategy.apply_env()
    mcp_config = build_mcp_config(PLUGIN_ROOT)
    checker = make_health_checker(mcp_config=mcp_config, session_id=parent_session_id, file_path=path)
    return checker.check(content, path, language, parent_session_id)
