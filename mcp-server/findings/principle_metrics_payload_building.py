"""Defines persisted payload construction for principle metrics."""

from typing import Protocol

from findings.principle_metrics import PrincipleMetrics


"""
solid-name: PrincipleMetricsPayloadBuilding
solid-category: abstraction
solid-description: Contract for constructing the persisted measurements for one principle.
"""
class PrincipleMetricsPayloadBuilding(Protocol):
    def build(self, metrics: PrincipleMetrics) -> dict: ...
