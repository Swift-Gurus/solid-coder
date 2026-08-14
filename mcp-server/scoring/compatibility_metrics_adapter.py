"""Adapts legacy unit metrics into typed measurements."""

from typing import Any

from findings.metric_additional_info import MetricAdditionalInfo
from findings.metric_value import MetricValue
from findings.principle_metrics import PrincipleMetrics
from scoring.compatibility_metrics_adapting import CompatibilityMetricsAdapting


"""
solid-name: CompatibilityMetricsAdapter
solid-category: boundary-adapter
solid-description: Adapts legacy unit metrics into typed principle measurements with audit context.
"""
class CompatibilityMetricsAdapter(CompatibilityMetricsAdapting):
    def adapt(
        self,
        unit_metrics: dict[str, Any],
        metric_id: str,
    ) -> PrincipleMetrics:
        return PrincipleMetrics(
            principle=metric_id.partition("-")[0],
            values=tuple(
                MetricValue(
                    name=name,
                    value=value,
                    is_exception=False,
                    additional_info=MetricAdditionalInfo(
                        reasoning="Submitted through the direct scoring compatibility API.",
                        evidence=f"Submitted metric value: {value}",
                    ),
                )
                for name, value in unit_metrics.items()
                if value is not None
            ),
        )
