"""Defines serialization for one typed condition variant."""

from __future__ import annotations

from typing import Protocol, TypeVar

from harness.condition_serializing import ConditionSerializing

ConditionT_contra = TypeVar("ConditionT_contra", contravariant=True)


"""
solid-name: ConditionVariantSerializing
solid-category: abstraction
solid-spec: [SPEC-037]
solid-description: Contract for serializing one supported condition variant.
"""


class ConditionVariantSerializing(Protocol[ConditionT_contra]):
    def serialize(
        self,
        condition: ConditionT_contra,
        nested_serializer: ConditionSerializing,
    ) -> dict[str, object]: ...
