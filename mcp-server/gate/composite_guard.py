"""
solid-description: Reports availability when all managed conditions pass.
solid-category: service
solid-tags: [hook, utility]
"""

from typing import Iterable

from guard_checking import GuardChecking


class CompositeGuard:
    """Guard: available only when every wrapped guard reports available."""

    def __init__(self, guards: Iterable[GuardChecking]) -> None:
        self._guards = list(guards)

    def is_available(self) -> bool:
        return all(guard.is_available() for guard in self._guards)
