"""
solid-description: Boundary adapter wrapping code_health_check._check to the HealthChecking protocol.
solid-category: service
solid-tags: [hook]
"""

import sys
from pathlib import Path
_HEALTH_DIR = Path(__file__).resolve().parent
_HOOKS_DIR = _HEALTH_DIR.parents[1] / 'hooks'
for _d in (_HOOKS_DIR, _HEALTH_DIR, _HEALTH_DIR / 'config', _HEALTH_DIR / 'llm', _HEALTH_DIR / 'codex'):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Callable, Optional


class CodeHealthCheckAdapter:
    """Boundary adapter: wraps the code_health_check module-level function for protocol-typed injection."""

    def __init__(self, check_fn: Callable) -> None:
        self._check = check_fn

    def check(self, content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
        return self._check(content, path, language, parent_session_id)
