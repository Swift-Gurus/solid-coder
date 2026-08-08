"""Defines concurrent dispatch of a dynamic handler collection."""

from typing import Protocol

from hook_decision import HookDecision
from hook_handling import HookHandling


"""
solid-name: HandlerDispatching
solid-category: abstraction
solid-description: Contract for executing a supplied handler collection and aggregating its authorization decisions.
solid-tags: [hook]
"""
class HandlerDispatching(Protocol):
    def __call__(self, handlers: list[HookHandling], event: dict) -> HookDecision: ...
