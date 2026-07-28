"""
solid-name: SimpleHookResponding
solid-category: abstraction
solid-tags: [hook]
solid-description: Contract for hook responders that allow or block without supporting input updates.
"""

from typing import Protocol


class SimpleHookResponding(Protocol):

    def allow(self) -> None: ...

    def block(self, reason: str, additional_context: str = "") -> None: ...