"""Defines included/excluded rule-selection evaluation."""

from typing import Protocol

from harness.rule_applicability_decision import (
    RuleApplicabilityDecision,
    RuleMatchDimension,
)
from harness.rule_selection import RuleSelection
from harness.rule_selection_requirement import RuleSelectionRequirement


"""
solid-name: RuleSelectionEvaluating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for evaluating rule-selection dimensions to determine applicability from candidates and requirements.
"""
class RuleSelectionEvaluating(Protocol):

    def evaluate(
        self,
        dimension: RuleMatchDimension,
        candidates: list[object],
        selection: RuleSelection,
        requirement: RuleSelectionRequirement,
    ) -> RuleApplicabilityDecision: ...
