"""
solid-description: Checks whether the configured LLM backend has the credentials to run.
solid-category: service
solid-tags: [hook, utility]
"""

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
