"""Defines client overrides for one engine-scored workflow metric."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from harness.metric_scoring_declaration import MetricScoringDeclaration


"""
solid-name: ReviewPolicyMetricOverride
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries optional metric enablement and complete typed scoring-band replacement.
"""
class ReviewPolicyMetricOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    id: str
    enabled: Optional[bool] = None
    reason: Optional[str] = None
    scoring: Optional[MetricScoringDeclaration] = None
