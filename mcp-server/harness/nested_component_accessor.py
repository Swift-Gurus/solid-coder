"""Reads one component from a nested runtime value."""

from __future__ import annotations

from collections.abc import Mapping

from harness.attribute_reading import AttributeReading
from harness.nested_component_accessing import NestedComponentAccessing
from harness.resolved_condition_value import ResolvedConditionValue


"""
solid-name: NestedComponentAccessor
solid-category: service
solid-spec: [SPEC-037]
solid-description: Reads one named component while preserving value presence.
"""
class NestedComponentAccessor(NestedComponentAccessing):
    def __init__(self, attribute_reader: AttributeReading) -> None:
        self._attribute_reader = attribute_reader

    def access(
        self,
        value: object,
        component: str,
    ) -> ResolvedConditionValue:
        if isinstance(value, Mapping):
            if component in value:
                return ResolvedConditionValue(present=True, value=value[component])
            return ResolvedConditionValue(present=False)
        return self._attribute_reader.read(value, component)
