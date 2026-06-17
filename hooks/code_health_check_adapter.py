"""
solid-description: Boundary adapter wrapping code_health_check._check to the HealthChecking protocol.
solid-category: service
solid-tags: [hook]
"""

from typing import Callable, Optional


class CodeHealthCheckAdapter:
    """Boundary adapter: wraps the code_health_check module-level function for protocol-typed injection."""

    def __init__(self, check_fn: Callable) -> None:
        self._check = check_fn

    def check(self, content: str, path: str, language: str, parent_session_id: str) -> Optional[list]:
        return self._check(content, path, language, parent_session_id)
