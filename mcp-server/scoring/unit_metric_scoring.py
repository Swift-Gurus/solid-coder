"""Defines typed scoring of one principle metric set."""

from typing import Protocol

from findings.principle_metrics import PrincipleMetrics
from scoring.metric_id_catalog import MetricIdCatalog
from scoring.unit_scoring_result import UnitScoringResult


"""
solid-name: UnitMetricScoring
solid-category: abstraction
solid-description: Contract for scoring immutable principle measurements against configured rule identifiers.
"""
class UnitMetricScoring(Protocol):
    @property
    def metric_ids(self) -> MetricIdCatalog: ...

    def score(
        self,
        metrics: PrincipleMetrics,
        metric_id: str,
        file_path: str,
    ) -> UnitScoringResult: ...
