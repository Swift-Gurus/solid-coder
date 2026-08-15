"""Compares one typed workflow condition against runtime context."""

from __future__ import annotations

from typing import Any

from harness.comparison_condition import ComparisonCondition
from harness.condition_reference_resolving import ConditionReferenceResolving
from harness.condition_runtime import ConditionRuntime
from harness.condition_value_matching import ConditionValueMatching


"""
solid-name: ConditionComparator
solid-category: service
solid-spec: [SPEC-037]
solid-description: Resolves and compares one workflow condition reference.
"""
class ConditionComparator(ConditionRuntime):
    def __init__(
        self,
        reference_resolver: ConditionReferenceResolving,
        value_matcher: ConditionValueMatching,
    ) -> None:
        self._reference_resolver = reference_resolver
        self._value_matcher = value_matcher

    def compare(
        self,
        condition: ComparisonCondition,
        context: dict[str, Any],
    ) -> bool:
        resolved = self._reference_resolver.resolve(condition.reference, context)
        return self._value_matcher.matches(
            condition.operator,
            resolved,
            condition.expected,
        )
