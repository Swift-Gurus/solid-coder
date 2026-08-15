"""Defines runtime comparison required by typed workflow conditions."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any, Protocol

if TYPE_CHECKING:
    from harness.comparison_condition import ComparisonCondition


"""
solid-name: ConditionRuntime
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving and comparing one workflow condition against runtime context.
"""
class ConditionRuntime(Protocol):
    def compare(
        self,
        condition: ComparisonCondition,
        context: dict[str, Any],
    ) -> bool: ...
