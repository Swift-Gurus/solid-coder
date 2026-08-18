"""Defines deterministic construction of one finalized rule review result."""

from typing import Protocol

from harness.rule_observations import RuleObservations
from harness.rule_review_result import RuleReviewResult


"""
solid-name: RuleReviewResultBuilding
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving an identified deterministic review result from validated rule observations.
"""
class RuleReviewResultBuilding(Protocol):
    def build(
        self,
        workflow_id: str,
        rule_instance_id: str,
        observations: RuleObservations,
    ) -> RuleReviewResult: ...
