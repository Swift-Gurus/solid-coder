"""Assembles the durable workflow condition serializer."""

from harness.all_condition_serializer import AllConditionSerializer
from harness.any_condition_serializer import AnyConditionSerializer
from harness.comparison_condition_serializer import ComparisonConditionSerializer
from harness.condition_serializer import ConditionSerializer
from harness.condition_serializing import ConditionSerializing
from harness.not_condition_serializer import NotConditionSerializer
from harness.unsupported_condition_serializer import UnsupportedConditionSerializer


def make_condition_serializer() -> ConditionSerializing:
    return ConditionSerializer(
        comparison_serializer=ComparisonConditionSerializer(),
        all_serializer=AllConditionSerializer(),
        any_serializer=AnyConditionSerializer(),
        not_serializer=NotConditionSerializer(),
        fallback_serializer=UnsupportedConditionSerializer(),
    )
