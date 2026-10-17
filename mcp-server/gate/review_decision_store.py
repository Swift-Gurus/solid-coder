"""Stores the current authorization decision for one file review."""

from hook_decision import HookDecision
from hook_context_buffer import HookContextBuffering


"""
solid-name: ReviewDecisionStore
solid-category: service
solid-description: Retains review warnings and authorization outcomes without allowing warnings to override a denial.
solid-tags: [hook]
"""
class ReviewDecisionStore:
    def __init__(self, context: HookContextBuffering) -> None:
        self._decision = HookDecision(allow=True)
        self._context = context

    def record_warning(self, message: str) -> None:
        self._context.append(message)

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
        return HookDecision(
            allow=self._decision.allow,
            reason=self._decision.reason,
            additional_context=self._context.render(self._decision.additional_context or "") or None,
        )
