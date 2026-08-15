"""Serializes one workflow comparison condition."""

from __future__ import annotations

from harness.comparison_condition import ComparisonCondition
from harness.condition_serializing import ConditionSerializing
from harness.condition_variant_serializing import ConditionVariantSerializing


"""
solid-name: ComparisonConditionSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Serializes a comparison condition into durable reversible data.
"""
class ComparisonConditionSerializer(
    ConditionVariantSerializing[ComparisonCondition]
):
    def serialize(
        self,
        condition: ComparisonCondition,
        nested_serializer: ConditionSerializing,
    ) -> dict[str, object]:
        return {
            "ref": condition.reference,
            condition.operator.value: condition.expected,
        }
