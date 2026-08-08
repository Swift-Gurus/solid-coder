"""Defines the immutable outcome of resolving a principle scorer."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

from scoring.unit_metric_scoring import UnitMetricScoring


"""
solid-name: PrincipleScorerResolution
solid-category: model
solid-description: Represents a principle-scoring resolution with either a successful outcome or failure information.
"""
@dataclass(frozen=True)
class PrincipleScorerResolution:
    scorer: Optional[UnitMetricScoring] = None
    principle_folder: Optional[Path] = None
    error_message: Optional[str] = None

    @property
    def succeeded(self) -> bool:
        return self.scorer is not None and self.error_message is None
