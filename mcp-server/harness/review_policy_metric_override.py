"""Defines client overrides for one engine-scored workflow metric."""

from harness.metric_scoring_declaration import MetricScoringDeclaration
from pydantic import BaseModel, ConfigDict

"""
solid-name: ReviewPolicyMetricOverride
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries optional metric enablement and complete typed scoring-band replacement.
"""


class ReviewPolicyMetricOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    enabled: bool | None = None
    reason: str | None = None
    scoring: MetricScoringDeclaration | None = None
