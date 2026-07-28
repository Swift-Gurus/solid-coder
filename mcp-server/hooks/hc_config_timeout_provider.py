"""
solid-description: Provides the LLM session timeout value.
solid-category: service
solid-tags: [hook]
"""

from typing import Callable


class HcConfigTimeoutProvider:
    """Reads [llm].timeout via an injected config-loading callable."""

    def __init__(self, config_loader: Callable) -> None:
        self._config_loader = config_loader

    def load_timeout(self) -> int:
        return self._config_loader().llm.timeout
