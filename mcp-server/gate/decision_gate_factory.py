"""Constructs non-terminating decision-capturing gates."""

from decision_capturing_gate import DecisionCapturingGate
from hook_decision_factory import HookDecisionFactory
from logging_protocol import Logging
from review_decision_store import ReviewDecisionStore


"""
solid-name: DecisionGateFactory
solid-category: factory
solid-description: Constructs non-terminating gates that capture authorization decisions.
solid-tags: [hook]
"""
class DecisionGateFactory:
    def create(self, logger: Logging) -> DecisionCapturingGate:
        return DecisionCapturingGate(
            logger=logger,
            decision_store=ReviewDecisionStore(
                decision_factory=HookDecisionFactory(),
            ),
        )
