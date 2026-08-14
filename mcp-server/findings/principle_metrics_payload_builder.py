"""Builds persisted payloads for one principle's metrics."""

from findings.metric_payload_building import MetricPayloadBuilding
from findings.principle_metrics import PrincipleMetrics
from findings.principle_metrics_payload_building import (
    PrincipleMetricsPayloadBuilding,
)


"""
solid-name: PrincipleMetricsPayloadBuilder
solid-category: boundary-adapter
solid-description: Builds persisted named measurements for one principle.
"""
class PrincipleMetricsPayloadBuilder(PrincipleMetricsPayloadBuilding):
    def __init__(self, metric_builder: MetricPayloadBuilding) -> None:
        self._metric_builder = metric_builder

    def build(self, metrics: PrincipleMetrics) -> dict:
        return {
            measurement.name: self._metric_builder.build(measurement)
            for measurement in metrics.values
        }
