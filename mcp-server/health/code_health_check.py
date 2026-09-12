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
from hc_runner_factory import select_strategy  # noqa: E402
from json_serializer import JsonSerializer  # noqa: E402
from mcp_config_builder import McpConfigBuilder  # noqa: E402
from mcp_config_profile import McpConfigProfile  # noqa: E402
from patch_review_context import PatchReviewContext  # noqa: E402
from workflow_health_checker_factory import WorkflowHealthCheckerFactory  # noqa: E402

SUPPORTED_EXTENSIONS: dict = {
    ".swift": "Swift",
    ".py": "Python",
}

"""
solid-name: CodeHealthCheck
solid-category: boundary
solid-spec: [SPEC-036, SPEC-041]
solid-description: Validates prospective source-health requests.
"""
class CodeHealthCheck:
    def __init__(self, service: CodeHealthCheckRequestChecking) -> None:
        self._service = service

    def check(
        self,
        content: str,
        path: str,
        language: str,
        parent_session_id: str,
        cwd: str = "",
        patch_context: Optional[PatchReviewContext] = None,
        principle_names: Optional[list[str]] = None,
    ) -> Optional[list]:
        return self._service.check(CodeHealthCheckRequest(
            content=content,
            path=path,
            language=language,
            parent_session_id=parent_session_id,
            cwd=cwd,
            patch_context=patch_context,
            principle_names=principle_names or [],
        ))


_CHECKER_FACTORY = WorkflowHealthCheckerFactory(PLUGIN_ROOT)
CHECK = CodeHealthCheck(CodeHealthCheckService(
    strategy_selector=select_strategy,
    checker_factory=_CHECKER_FACTORY.make,
    mcp_config=McpConfigBuilder(
        project_root=PLUGIN_ROOT,
        profile=McpConfigProfile.GATE_FLOW,
        serializer=JsonSerializer(),
    ).build(),
))
