"""
solid-description: Contract for retrieving the LLM session timeout value.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class ConfigProvider(Protocol):
    """Supplies the LLM session timeout, keeping hc_config an implementation detail."""

    def load_timeout(self) -> int: ...
