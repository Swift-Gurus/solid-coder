"""Defines lookup of named measurements within principle metrics."""

from typing import Optional, Protocol

from findings.metric_value import MetricValue
from findings.principle_metrics import PrincipleMetrics


"""
solid-name: MetricMeasurementResolving
solid-category: abstraction
solid-description: Contract for resolving one named measurement from typed principle metrics.
"""
class MetricMeasurementResolving(Protocol):
    def resolve(self, metrics: PrincipleMetrics, name: str) -> Optional[MetricValue]: ...
