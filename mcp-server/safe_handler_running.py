"""
solid-name: SafeHandlerRunning
solid-category: abstraction
solid-description: Contract for safe handler execution that prevents exceptions from propagating to the caller.
solid-tags: [hook]
"""

from typing import Protocol

from hook_decision import HookDecision
from hook_handling import HookHandling


class SafeHandlerRunning(Protocol):
    def run(self, handler: HookHandling, event: dict) -> HookDecision: ...
