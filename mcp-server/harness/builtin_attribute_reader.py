"""Adapts Python attribute lookup for workflow runtime values."""

from __future__ import annotations

from harness.attribute_reading import AttributeReading
from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: BuiltinAttributeReader
solid-category: adapter
solid-spec: [SPEC-037]
solid-description: Adapts runtime attribute lookup into a presence-aware result.
"""
class BuiltinAttributeReader(AttributeReading):
    def read(
        self,
        value: object,
        attribute: str,
    ) -> ResolvedConditionValue:
        try:
            return ResolvedConditionValue(
                present=True,
                value=getattr(value, attribute),
            )
        except AttributeError:
            return ResolvedConditionValue(present=False)
