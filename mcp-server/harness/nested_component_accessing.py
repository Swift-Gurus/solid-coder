"""Defines access to one component of a nested runtime value."""

from __future__ import annotations

from typing import Protocol

from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: NestedComponentAccessing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for reading one named component from a runtime value.
"""
class NestedComponentAccessing(Protocol):
    def access(
        self,
        value: object,
        component: str,
    ) -> ResolvedConditionValue: ...
