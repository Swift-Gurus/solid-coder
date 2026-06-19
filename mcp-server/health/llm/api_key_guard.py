"""
solid-description: Checks whether the configured LLM backend has the credentials to run.
solid-category: service
solid-tags: [hook, utility]
"""

import sys
from pathlib import Path
_HOOKS_DIR = Path(__file__).resolve().parents[3] / 'hooks'
_MODULE_DIR = Path(__file__).resolve().parent
for _d in (_HOOKS_DIR, _MODULE_DIR):
    if str(_d) not in sys.path:
        sys.path.insert(0, str(_d))

from typing import Callable


class ApiKeyGuard:
    """Determines whether the configured LLM backend can authenticate."""

    def __init__(
        self,
        backend_fn: Callable[[], str],
        api_key_fn: Callable[[], str],
    ) -> None:
        self._backend = backend_fn
        self._api_key = api_key_fn

    def is_available(self) -> bool:
        if self._backend().lower() != "claude":
            return True
        return bool(self._api_key().strip())
