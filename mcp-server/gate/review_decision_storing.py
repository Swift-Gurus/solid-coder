"""Defines mutable storage of one file-review decision."""

from typing import Protocol

from hook_decision import HookDecision


"""
solid-name: ReviewDecisionStoring
solid-category: abstraction
solid-description: Contract for recording and retrieving the current authorization decision for one review.
solid-tags: [hook]
"""
class ReviewDecisionStoring(Protocol):
    def record_allow(self, additional_context: str = "") -> None: ...
    def record_denial(self, reason: str, additional_context: str = "") -> None: ...
    def current(self) -> HookDecision: ...
