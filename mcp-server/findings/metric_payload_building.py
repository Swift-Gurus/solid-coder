"""Defines persisted payload construction for one metric."""

from typing import Protocol

from findings.metric_value import MetricValue


"""
solid-name: MetricPayloadBuilding
solid-category: abstraction
solid-description: Contract for constructing the persisted payload for one metric measurement.
"""
class MetricPayloadBuilding(Protocol):
    def build(self, measurement: MetricValue) -> dict: ...
