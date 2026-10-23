"""Defines scoring authored beside one observation-producing step."""

from __future__ import annotations

from typing import Annotated

from harness.metric_scoring_declaration import MetricScoringDeclaration
from pydantic import Field, StringConstraints

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
    condition: object | None = Field(
        default=None,
        validation_alias="when",
        serialization_alias="when",
    )
    reducer: object | None = None
