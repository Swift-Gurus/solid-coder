"""Defines one schema-validated DRY reuse assessment."""

from pydantic import BaseModel, ConfigDict, Field

from dry_reuse_classification import DRYReuseClassification


"""
solid-name: DRYReuseAssessment
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries a candidate reuse decision with the reasoning and evidence required for audit.
"""
class DRYReuseAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    classification: DRYReuseClassification
    reasoning: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
