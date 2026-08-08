"""Captures a gate response without terminating the hook process."""

from typing import Optional

from hook_decision import HookDecision
from logging_protocol import Logging
from review_decision_storing import ReviewDecisionStoring


"""
solid-name: DecisionCapturingGate
solid-category: service
solid-description: Delegates review outcome storage and diagnostic logging for one non-terminating gate evaluation.
solid-tags: [hook]
"""
class DecisionCapturingGate:
    def __init__(
        self,
        logger: Logging,
        decision_store: ReviewDecisionStoring,
    ) -> None:
        self._logger = logger
        self._decision_store = decision_store

    @property
    def decision(self) -> HookDecision:
        return self._decision_store.current()

    def log(self, message: str) -> None:
        self._logger.log(message)

    def allow(
        self,
        additional_context: str = "",
        updated_input: Optional[dict] = None,
    ) -> None:
        self._decision_store.record_allow(additional_context)

    def block(self, reason: str, additional_context: str = "") -> None:
        self._decision_store.record_denial(reason, additional_context)
