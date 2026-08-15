"""Applies type-strict workflow condition comparisons."""

from __future__ import annotations

from harness.condition_operator import ConditionOperator
from harness.condition_value_matching import ConditionValueMatching
from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: ConditionValueMatcher
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies supported workflow comparison semantics without type coercion.
"""
class ConditionValueMatcher(ConditionValueMatching):
    def matches(
        self,
        operator: ConditionOperator,
        resolved: ResolvedConditionValue,
        expected: object,
    ) -> bool:
        if operator is ConditionOperator.EXISTS:
            return resolved.present is expected
        if not resolved.present:
            return False
        if operator is ConditionOperator.EQUALS:
            return self._equal(resolved.value, expected)
        if operator is ConditionOperator.NOT_EQUALS:
            return not self._equal(resolved.value, expected)
        if operator is ConditionOperator.IN:
            return self._contains(expected, resolved.value)
        if operator is ConditionOperator.NOT_IN:
            return not self._contains(expected, resolved.value)
        raise TypeError(f"Unsupported condition operator: {operator.value}")

    def _contains(self, collection: object, value: object) -> bool:
        if not isinstance(collection, list):
            return False
        return any(self._equal(value, candidate) for candidate in collection)

    def _equal(self, actual: object, expected: object) -> bool:
        return type(actual) is type(expected) and actual == expected
