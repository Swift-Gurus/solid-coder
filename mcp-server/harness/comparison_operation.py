"""Defines one parsed workflow comparison operation."""

from dataclasses import dataclass

from harness.condition_operator import ConditionOperator


"""
solid-name: ComparisonOperation
solid-category: model
solid-spec: [SPEC-037]
solid-description: Represents a validated workflow comparison operator and expected value.
"""
@dataclass(frozen=True)
class ComparisonOperation:
    operator: ConditionOperator
    expected: object
