"""Applies type-strict workflow condition comparisons."""

from __future__ import annotations

from harness.collection_value_matching import CollectionValueMatching
from harness.condition_operator import ConditionOperator
from harness.condition_value_matching import ConditionValueMatching
from harness.resolved_condition_value import ResolvedConditionValue
from harness.strict_value_comparing import StrictValueComparing


"""
solid-name: ConditionValueMatcher
solid-category: service
solid-spec: [SPEC-037]
solid-description: Applies supported workflow comparison semantics without type coercion.
"""
class ConditionValueMatcher(ConditionValueMatching):
    def __init__(
        self,
        comparator: StrictValueComparing,
        collection_matcher: CollectionValueMatching,
    ) -> None:
        self._comparator = comparator
        self._collection_matcher = collection_matcher

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
            return self._comparator.equal(resolved.value, expected)
        if operator is ConditionOperator.NOT_EQUALS:
            return not self._comparator.equal(resolved.value, expected)
        if operator is ConditionOperator.IN:
            return self._collection_matcher.contains(expected, resolved.value)
        if operator is ConditionOperator.NOT_IN:
            return not self._collection_matcher.contains(expected, resolved.value)
        if operator is ConditionOperator.CONTAINS:
            return self._collection_matcher.contains(resolved.value, expected)
        if operator is ConditionOperator.NOT_CONTAINS:
            return not self._collection_matcher.contains(resolved.value, expected)
        raise TypeError(f"Unsupported condition operator: {operator.value}")
