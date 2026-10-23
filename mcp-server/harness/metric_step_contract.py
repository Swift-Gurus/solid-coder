"""Defines the decoded contract for one metric workflow step."""

from __future__ import annotations

from dataclasses import dataclass

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.metric_declaration import MetricDeclaration

"""
solid-name: MetricStepContract
solid-category: model
solid-spec: [SPEC-053]
solid-description: Represents the complete typed contract for a metric workflow step.
"""


@dataclass(frozen=True)
class MetricStepContract:
    metric: MetricDeclaration
    calculation: CollectionMetricCalculation | None = None
