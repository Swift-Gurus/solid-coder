"""Defines planning of applicable handlers for a patch request."""

from typing import Protocol

from hook_handling import HookHandling


"""
solid-name: PatchHandlerPlanning
solid-category: abstraction
solid-description: Contract for translating one patch request into applicable per-file review handlers.
solid-tags: [hook]
"""
class PatchHandlerPlanning(Protocol):
    def plan(self, tool_input: dict) -> list[HookHandling]: ...
