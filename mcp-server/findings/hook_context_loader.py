"""
solid-name: FileSystemHookContextLoader
solid-category: service
solid-description: Loads context from the filesystem as an injectable service.
"""

from __future__ import annotations

from typing import Callable, Optional

from findings.gateway_handler import _load_hook_context
from findings.unit_coverage_validator import HookContextLoading


class FileSystemHookContextLoader(HookContextLoading):
    """Protocol adapter: wraps _load_hook_context() as an injectable HookContextLoading.

    Provides a seam for testing — callers inject FileSystemHookContextLoader in
    production and a mock/stub in tests, without importing the module-level function.
    """

    def __init__(self, loader_fn: Optional[Callable] = None) -> None:
        self._load = loader_fn or _load_hook_context

    def load(self) -> Optional[dict]:
        return self._load()
