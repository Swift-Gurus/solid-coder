"""
solid-description: Validates source code in a language-specific manner.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path

_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (
    _MCP_DIR,
    _HEALTH_DIR,
    _HEALTH_DIR / "config",
    _HEALTH_DIR / "llm",
    _HEALTH_DIR / "codex",
):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from code_health_check_request import CodeHealthCheckRequest
from code_health_check_request_checking import CodeHealthCheckRequestChecking
from code_health_check_service import CodeHealthCheckService
from configured_health_checker_factory import ConfiguredHealthCheckerFactory
from health.config.hc_config_core import find_repository_root
from health_check_outcome import HealthCheckOutcome
from hook_utils import PLUGIN_ROOT, _resolve_project_root
from patch_review_context import PatchReviewContext
from source.repository_target_resolver import RepositoryTargetResolver

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
        patch_context: PatchReviewContext | None = None,
        principle_names: list[str] | None = None,
    ) -> HealthCheckOutcome:
        return self._service.check(
            CodeHealthCheckRequest(
                content=content,
                path=path,
                language=language,
                parent_session_id=parent_session_id,
                cwd=cwd,
                patch_context=patch_context,
                principle_names=principle_names or [],
            )
        )


_CHECKER_FACTORY = ConfiguredHealthCheckerFactory(PLUGIN_ROOT)
CHECK = CodeHealthCheck(
    CodeHealthCheckService(
        checker_factory=_CHECKER_FACTORY,
        targets=RepositoryTargetResolver(find_repository_root),
        current_directory=_resolve_project_root,
    )
)
