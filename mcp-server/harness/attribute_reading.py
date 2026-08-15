"""Defines named attribute reading for runtime values."""

from __future__ import annotations

from typing import Protocol

from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: AttributeReading
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for reading a named attribute while preserving its presence.
"""
class AttributeReading(Protocol):
    def read(
        self,
        value: object,
        attribute: str,
    ) -> ResolvedConditionValue: ...
