"""Defines condition reference resolution."""

from __future__ import annotations

from typing import Any, Protocol

from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: ConditionReferenceResolving
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for resolving workflow condition references with presence information.
"""
class ConditionReferenceResolving(Protocol):
    def resolve(
        self,
        reference: str,
        context: dict[str, Any],
    ) -> ResolvedConditionValue: ...
