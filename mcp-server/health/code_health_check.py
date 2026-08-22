"""
solid-description: Validates source code in a language-specific manner.
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
from code_health_check_request import CodeHealthCheckRequest  # noqa: E402
from code_health_check_request_checking import CodeHealthCheckRequestChecking  # noqa: E402
from code_health_check_service import CodeHealthCheckService  # noqa: E402
from hc_checker_factory import make_health_checker  # noqa: E402
from hc_runner_factory import select_strategy  # noqa: E402
from mcp_config_builder import build_mcp_config  # noqa: E402
from patch_review_context import PatchReviewContext  # noqa: E402

SUPPORTED_EXTENSIONS: dict = {
    ".swift": "Swift",
    ".py": "Python",
}

_SERVICE = CodeHealthCheckService(
    strategy_selector=lambda: select_strategy(),
    mcp_config_builder=lambda root: build_mcp_config(root),
    checker_factory=lambda **arguments: make_health_checker(**arguments),
    plugin_root=PLUGIN_ROOT,
)


def _check(
    content: str,
    path: str,
    language: str,
    parent_session_id: str,
    cwd: str = "",
    patch_context: Optional[PatchReviewContext] = None,
    service: CodeHealthCheckRequestChecking = _SERVICE,
) -> Optional[list]:
    return service.check(CodeHealthCheckRequest(
        content=content,
        path=path,
        language=language,
        parent_session_id=parent_session_id,
        cwd=cwd,
        patch_context=patch_context,
    ))
