"""Defines the metric value types accepted by a reducer."""

from dataclasses import dataclass

from harness.metric_value_type import MetricValueType

"""
solid-name: MetricReducerValueCompatibility
solid-category: model
solid-spec: [SPEC-054, SPEC-059]
solid-description: Defines accepted metric value types and their validation diagnostic.
"""


@dataclass(frozen=True)
class MetricReducerValueCompatibility:
    allowed_types: list[MetricValueType]
    expected_description: str
