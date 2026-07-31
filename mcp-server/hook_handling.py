"""
solid-name: HookHandling
solid-category: abstraction
solid-description: Contract for handlers that determine whether to process events and report handling decisions.
solid-tags: [hook]
"""

from typing import Protocol

from hook_decision import HookDecision


class HookHandling(Protocol):
    def should_handle(self, event: dict) -> bool: ...

    def handle(self, event: dict) -> HookDecision: ...
