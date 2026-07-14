"""
solid-description: Loads LLM session timeout from configuration.
solid-category: service
solid-tags: [hook]
"""

from typing import Callable


class HcConfigTimeoutProvider:
    """Reads [llm].bare_session_timeout via an injected config-loading callable."""

    def __init__(self, config_loader: Callable) -> None:
        self._config_loader = config_loader

    def load_timeout(self) -> int:
        return self._config_loader().llm.bare_session_timeout