"""Defines the immutable outcome of resolving a principle scorer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from scoring.unit_metric_scoring import UnitMetricScoring

"""
solid-name: PrincipleScorerResolution
solid-category: model
solid-description: Represents a principle-scoring resolution with either a successful outcome or failure information.
"""


@dataclass(frozen=True)
class PrincipleScorerResolution:
    scorer: UnitMetricScoring | None = None
    principle_folder: Path | None = None
    error_message: str | None = None

    @property
    def succeeded(self) -> bool:
        return self.scorer is not None and self.error_message is None
