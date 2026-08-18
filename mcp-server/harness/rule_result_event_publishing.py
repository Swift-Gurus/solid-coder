"""Defines audit-event publication for one finalized rule result."""

from typing import Protocol

from harness.rule_review_result import RuleReviewResult


"""
solid-name: RuleResultEventPublishing
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for publishing auditable events from a finalized rule result.
"""
class RuleResultEventPublishing(Protocol):
    def publish(
        self,
        events_path: str,
        result: RuleReviewResult,
    ) -> None: ...
