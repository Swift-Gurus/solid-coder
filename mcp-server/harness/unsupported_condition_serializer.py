"""Rejects unsupported condition types during durable serialization."""

from __future__ import annotations

from harness.condition_declaration import ConditionDeclaration
from harness.condition_serializing import ConditionSerializing
from harness.condition_variant_serializing import ConditionVariantSerializing


"""
solid-name: UnsupportedConditionSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Rejects a condition type without a registered durable representation.
"""
class UnsupportedConditionSerializer(
    ConditionVariantSerializing[ConditionDeclaration]
):
    def serialize(
        self,
        condition: ConditionDeclaration,
        nested_serializer: ConditionSerializing,
    ) -> dict[str, object]:
        raise TypeError(
            f"Unsupported condition type: {type(condition).__name__}"
        )
