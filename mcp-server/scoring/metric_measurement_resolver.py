"""Resolves named measurements from typed principle metrics."""

from findings.metric_value import MetricValue
from findings.principle_metrics import PrincipleMetrics

from scoring.metric_measurement_resolving import MetricMeasurementResolving

"""
solid-name: MetricMeasurementResolver
solid-category: service
solid-description: Resolves one named measurement from typed principle metrics.
"""


class MetricMeasurementResolver(MetricMeasurementResolving):
    def resolve(self, metrics: PrincipleMetrics, name: str) -> MetricValue | None:
        return next(
            (measurement for measurement in metrics.values if measurement.name == name),
            None,
        )
