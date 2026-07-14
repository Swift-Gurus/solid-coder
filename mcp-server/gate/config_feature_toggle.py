"""
solid-description: Determines whether a feature flag is enabled.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Callable


class ConfigFeatureToggle:
    """Guard: available only when the configured feature flag is enabled."""

    def __init__(self, enabled_fn: Callable[[], bool]) -> None:
        self._enabled = enabled_fn

    def is_available(self) -> bool:
        return self._enabled()