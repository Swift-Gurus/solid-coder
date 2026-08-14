"""Defines adaptation of legacy unit metrics into typed measurements."""

from typing import Any, Protocol

from findings.principle_metrics import PrincipleMetrics


"""
solid-name: CompatibilityMetricsAdapting
solid-category: abstraction
solid-description: Contract for adapting legacy unit metrics into typed principle measurements.
"""
class CompatibilityMetricsAdapting(Protocol):
    def adapt(
        self,
        unit_metrics: dict[str, Any],
        metric_id: str,
    ) -> PrincipleMetrics: ...
