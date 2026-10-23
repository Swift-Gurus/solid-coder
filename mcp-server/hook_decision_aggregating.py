"""
solid-name: DecisionAggregating
solid-category: abstraction
solid-description: Contract for consolidating multiple decisions into a single outcome.
solid-tags: [hook]
"""

from typing import Protocol

from hook_decision import HookDecision


class DecisionAggregating(Protocol):
    def aggregate(self, decisions: list[HookDecision]) -> HookDecision: ...
