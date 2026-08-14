"""Defines construction of configured typed metric scorers."""

from pathlib import Path
from typing import Protocol

from scoring.unit_metric_scoring import UnitMetricScoring


"""
solid-name: UnitMetricScorerCreating
solid-category: abstraction
solid-description: Contract for creating a typed metric scorer for one principle folder.
"""
class UnitMetricScorerCreating(Protocol):
    def make(self, principle_folder: Path) -> UnitMetricScoring: ...
