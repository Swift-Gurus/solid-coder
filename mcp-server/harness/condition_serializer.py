"""Routes typed workflow conditions to durable serializers."""

from __future__ import annotations

from functools import singledispatchmethod

from harness.all_condition import AllCondition
from harness.any_condition import AnyCondition
from harness.comparison_condition import ComparisonCondition
from harness.condition_declaration import ConditionDeclaration
from harness.condition_serializing import ConditionSerializing
from harness.condition_variant_serializing import ConditionVariantSerializing
from harness.not_condition import NotCondition


"""
solid-name: ConditionSerializer
solid-category: boundary
solid-spec: [SPEC-037]
solid-description: Routes typed workflow conditions to their durable serializers.
"""
class ConditionSerializer(ConditionSerializing):
    def __init__(
        self,
        comparison_serializer: ConditionVariantSerializing[ComparisonCondition],
        all_serializer: ConditionVariantSerializing[AllCondition],
        any_serializer: ConditionVariantSerializing[AnyCondition],
        not_serializer: ConditionVariantSerializing[NotCondition],
        fallback_serializer: ConditionVariantSerializing[ConditionDeclaration],
    ) -> None:
        self._comparison_serializer = comparison_serializer
        self._all_serializer = all_serializer
        self._any_serializer = any_serializer
        self._not_serializer = not_serializer
        self._fallback_serializer = fallback_serializer

    @singledispatchmethod
    def serialize(
        self,
        condition: ConditionDeclaration,
    ) -> dict[str, object]:
        return self._fallback_serializer.serialize(condition, self)

    @serialize.register(ComparisonCondition)
    def _serialize_comparison(
        self,
        condition: ComparisonCondition,
    ) -> dict[str, object]:
        return self._comparison_serializer.serialize(condition, self)

    @serialize.register(AllCondition)
    def _serialize_all(self, condition: AllCondition) -> dict[str, object]:
        return self._all_serializer.serialize(condition, self)

    @serialize.register(AnyCondition)
    def _serialize_any(self, condition: AnyCondition) -> dict[str, object]:
        return self._any_serializer.serialize(condition, self)

    @serialize.register(NotCondition)
    def _serialize_not(self, condition: NotCondition) -> dict[str, object]:
        return self._not_serializer.serialize(condition, self)
