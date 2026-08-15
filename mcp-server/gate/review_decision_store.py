"""Stores the current authorization decision for one file review."""

from hook_decision import HookDecision


"""
solid-name: ReviewDecisionStore
solid-category: service
solid-description: Records allow or deny outcomes and exposes the current immutable review decision.
solid-tags: [hook]
"""
class ReviewDecisionStore:
    def __init__(self) -> None:
        self._decision = HookDecision(allow=True)

    def record_allow(self, additional_context: str = "") -> None:
        if self._decision.allow:
            self._decision = HookDecision(
                allow=True,
                additional_context=additional_context or None,
            )

    def record_denial(self, reason: str, additional_context: str = "") -> None:
        self._decision = HookDecision(
            allow=False,
            reason=reason,
            additional_context=additional_context or None,
        )

    def current(self) -> HookDecision:
        return self._decision
