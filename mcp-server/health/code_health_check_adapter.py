"""
solid-description: Enables code health checking on provided content.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_MCP_DIR = _HEALTH_DIR.parent
for _d in (_MCP_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Optional

from hc_checker import HealthChecking
from patch_review_context import PatchReviewContext


"""
solid-name: CodeHealthCheckAdapter
solid-description: Enables injectable code-health checking for prospective source content.
solid-category: service
solid-tags: [hook]
"""
class CodeHealthCheckAdapter:
    """Binds one patch context while preserving the health-checking interface."""

    def __init__(
        self,
        checker: HealthChecking,
        patch_context: Optional[PatchReviewContext] = None,
    ) -> None:
        self._checker = checker
        self._patch_context = patch_context

    def check(self, content: str, path: str, language: str, parent_session_id: str, cwd: str = "") -> Optional[list]:
        return self._checker.check(
            content,
            path,
            language,
            parent_session_id,
            cwd,
            patch_context=self._patch_context,
        )
