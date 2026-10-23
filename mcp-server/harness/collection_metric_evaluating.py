"""Defines deterministic collection metric evaluation."""

from typing import Protocol

from harness.collection_metric_calculation import CollectionMetricCalculation
from harness.workflow_run_context import WorkflowRunContext

"""
solid-name: CollectionMetricEvaluating
solid-category: abstraction
solid-spec: [SPEC-053]
solid-description: Contract for deterministically evaluating a collection-backed metric.
"""


class CollectionMetricEvaluating(Protocol):
    def evaluate(
        self,
        calculation: CollectionMetricCalculation,
        entries: list[object],
        context: WorkflowRunContext,
    ) -> CollectionMetricCalculation: ...
