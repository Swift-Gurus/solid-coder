"""Defines scoring authored beside one observation-producing step."""

from __future__ import annotations

from typing import Annotated, Optional

from pydantic import Field, StringConstraints

from harness.metric_scoring_declaration import MetricScoringDeclaration


LocalOutputName = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


"""
solid-name: CoLocatedMetricScoringDeclaration
solid-category: model
solid-spec: [SPEC-058]
solid-description: Extends deterministic severity scoring with an owning-step output source.
"""
class CoLocatedMetricScoringDeclaration(MetricScoringDeclaration):
    source: LocalOutputName
    condition: Optional[object] = Field(
        default=None,
        validation_alias="when",
        serialization_alias="when",
    )
    reducer: Optional[object] = None
