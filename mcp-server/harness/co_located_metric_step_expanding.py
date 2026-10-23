"""Defines expansion of one typed compact-metric owner."""

from __future__ import annotations

from typing import Protocol

from harness.co_located_metric_step_expansion import CoLocatedMetricStepExpansion
from harness.step_declaration import StepDeclaration

"""
solid-name: CoLocatedMetricStepExpanding
solid-category: abstraction
solid-spec: [SPEC-058]
solid-description: Contract for producing canonical metric steps from one validated measurement owner.
"""


class CoLocatedMetricStepExpanding(Protocol):
    def expand(
        self,
        owner: StepDeclaration,
        owner_id: str,
        owning_alias: str | None,
    ) -> CoLocatedMetricStepExpansion: ...
