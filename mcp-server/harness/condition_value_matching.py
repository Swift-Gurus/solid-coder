"""Defines type-strict condition value matching."""

from __future__ import annotations

from typing import Protocol

from harness.condition_operator import ConditionOperator
from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: ConditionValueMatching
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for applying workflow comparison operators to resolved condition values.
"""
class ConditionValueMatching(Protocol):
    def matches(
        self,
        operator: ConditionOperator,
        resolved: ResolvedConditionValue,
        expected: object,
    ) -> bool: ...
