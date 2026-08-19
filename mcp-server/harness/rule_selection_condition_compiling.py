"""Defines compilation of one rule selector into workflow conditions."""

from typing import Protocol

from harness.comparison_condition import ComparisonCondition
from harness.condition_operator import ConditionOperator


"""
solid-name: RuleSelectionConditionCompiling
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for translating included and excluded rule values into comparison conditions.
"""
class RuleSelectionConditionCompiling(Protocol):
    def compile(
        self,
        reference: str,
        included: list[object],
        excluded: list[object],
        inclusion_operator: ConditionOperator,
        exclusion_operator: ConditionOperator,
    ) -> list[ComparisonCondition]: ...
