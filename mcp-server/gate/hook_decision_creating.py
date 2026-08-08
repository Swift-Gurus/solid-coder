"""Defines construction of hook authorization decisions."""

from typing import Optional, Protocol

from hook_decision import HookDecision


"""
solid-name: HookDecisionCreating
solid-category: abstraction
solid-description: Contract for constructing authorization decisions with optional reasons and context.
solid-tags: [hook]
"""
class HookDecisionCreating(Protocol):
    def create(
        self,
        allow: bool,
        reason: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> HookDecision: ...
