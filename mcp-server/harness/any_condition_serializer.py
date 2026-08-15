"""Serializes a disjunction of workflow conditions."""

from __future__ import annotations

from harness.any_condition import AnyCondition
from harness.condition_serializing import ConditionSerializing
from harness.condition_variant_serializing import ConditionVariantSerializing


"""
solid-name: AnyConditionSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Serializes a disjunction condition into durable reversible data.
"""
class AnyConditionSerializer(ConditionVariantSerializing[AnyCondition]):
    def serialize(
        self,
        condition: AnyCondition,
        nested_serializer: ConditionSerializing,
    ) -> dict[str, object]:
        return {
            "any": [
                nested_serializer.serialize(nested)
                for nested in condition.conditions
            ]
        }
