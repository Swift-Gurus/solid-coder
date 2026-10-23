"""Defines rendering of metric derivation audit payloads."""

from typing import Protocol

from harness.collection_metric_calculation import CollectionMetricCalculation

"""
solid-name: MetricDerivationRendering
solid-category: abstraction
solid-spec: [SPEC-053]
solid-description: Contract for rendering durable metric derivation audit payloads.
"""


class MetricDerivationRendering(Protocol):
    def render(
        self,
        calculation: CollectionMetricCalculation | None,
    ) -> dict | None: ...
