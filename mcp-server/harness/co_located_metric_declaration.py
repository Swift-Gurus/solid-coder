"""Defines one compact metric authored beside its observation producer."""

from typing import Annotated

from pydantic import StringConstraints

from harness.co_located_metric_scoring_declaration import (
    CoLocatedMetricScoringDeclaration,
)
from harness.metric_declaration import MetricDeclaration


CoLocatedMetricStepId = Annotated[
    str,
    StringConstraints(strip_whitespace=True, min_length=1),
]


"""
solid-name: CoLocatedMetricDeclaration
solid-category: model
solid-spec: [SPEC-058]
solid-description: Adds runtime step identity and an owning-step output source to the existing metric contract.
"""
class CoLocatedMetricDeclaration(MetricDeclaration):
    id: CoLocatedMetricStepId
    scoring: CoLocatedMetricScoringDeclaration
