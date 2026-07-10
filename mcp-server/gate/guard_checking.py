"""
solid-description: Contract for checking whether a resource is available.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class GuardChecking(Protocol):
    def is_available(self) -> bool: ...
