"""
solid-name: HandlerExecuting
solid-category: abstraction
solid-description: Contract for executing hooks against an event and returning decisions.
solid-tags: [hook]
"""

from typing import List, Protocol

from hook_decision import HookDecision


class HandlerExecuting(Protocol):
    def run(self, event: dict) -> List[HookDecision]: ...
