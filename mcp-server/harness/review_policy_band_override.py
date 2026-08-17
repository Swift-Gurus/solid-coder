"""Defines one client-authored scoring-band override."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from harness.scoring_band_severity import ScoringBandSeverity
from harness.scoring_comparison_operator import ScoringComparisonOperator


"""
solid-name: ReviewPolicyBandOverride
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries one typed severity, comparison, value, and optional audit reason override.
"""
class ReviewPolicyBandOverride(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    severity: ScoringBandSeverity
    operator: ScoringComparisonOperator
    value: object
    reason: Optional[str] = None
