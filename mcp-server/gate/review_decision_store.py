"""Stores the current authorization decision for one file review."""

from hook_decision import HookDecision
from hook_decision_creating import HookDecisionCreating


"""
solid-name: ReviewDecisionStore
solid-category: service
solid-description: Records allow or deny outcomes and exposes the current immutable review decision.
solid-tags: [hook]
"""
class ReviewDecisionStore:
    def __init__(self, decision_factory: HookDecisionCreating) -> None:
        self._decision_factory = decision_factory
        self._decision = decision_factory.create(allow=True)

    def record_allow(self, additional_context: str = "") -> None:
        if self._decision.allow:
            self._decision = self._decision_factory.create(
                allow=True,
                additional_context=additional_context or None,
            )

    def record_denial(self, reason: str, additional_context: str = "") -> None:
        self._decision = self._decision_factory.create(
            allow=False,
            reason=reason,
            additional_context=additional_context or None,
        )

    def current(self) -> HookDecision:
        return self._decision
