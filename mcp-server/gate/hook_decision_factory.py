"""Constructs hook authorization decisions."""

from typing import Optional

from hook_decision import HookDecision


"""
solid-name: HookDecisionFactory
solid-category: factory
solid-description: Constructs immutable authorization decisions from outcome, reason, and context values.
solid-tags: [hook]
"""
class HookDecisionFactory:
    def create(
        self,
        allow: bool,
        reason: Optional[str] = None,
        additional_context: Optional[str] = None,
    ) -> HookDecision:
        return HookDecision(
            allow=allow,
            reason=reason,
            additional_context=additional_context,
        )
