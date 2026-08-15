"""Serializes a negated workflow condition."""

from __future__ import annotations

from harness.condition_serializing import ConditionSerializing
from harness.condition_variant_serializing import ConditionVariantSerializing
from harness.not_condition import NotCondition


"""
solid-name: NotConditionSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Serializes a negated condition into durable reversible data.
"""
class NotConditionSerializer(ConditionVariantSerializing[NotCondition]):
    def serialize(
        self,
        condition: NotCondition,
        nested_serializer: ConditionSerializing,
    ) -> dict[str, object]:
        return {"not": nested_serializer.serialize(condition.condition)}
