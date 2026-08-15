"""Serializes a conjunction of workflow conditions."""

from __future__ import annotations

from harness.all_condition import AllCondition
from harness.condition_serializing import ConditionSerializing
from harness.condition_variant_serializing import ConditionVariantSerializing


"""
solid-name: AllConditionSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Serializes a conjunction condition into durable reversible data.
"""
class AllConditionSerializer(ConditionVariantSerializing[AllCondition]):
    def serialize(
        self,
        condition: AllCondition,
        nested_serializer: ConditionSerializing,
    ) -> dict[str, object]:
        return {
            "all": [
                nested_serializer.serialize(nested)
                for nested in condition.conditions
            ]
        }
