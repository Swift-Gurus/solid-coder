"""
solid-description: Determines whether the configured LLM backend can authenticate.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_MCP_DIR = Path(__file__).resolve().parents[2]
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_MCP_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Callable
from utils.debug_logger import Observing


class ApiKeyGuard:
    """Determines whether the configured LLM backend can authenticate."""

    def __init__(
        self,
        backend_fn: Callable[[], str],
        api_key_fn: Callable[[], str],
    ) -> None:
        self._backend = backend_fn
        self._api_key = api_key_fn

    @Observing("gate.api_key_guard.is_available")
    def is_available(self) -> bool:
        if self._backend().lower() != "claude":
            return True
        return bool(self._api_key().strip())
