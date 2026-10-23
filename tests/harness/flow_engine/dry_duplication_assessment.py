"""Defines one schema-validated DRY implementation-duplication assessment."""

from dry_duplication_classification import DRYDuplicationClassification
from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: DRYDuplicationAssessment
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries an implementation-duplication decision with the reasoning and evidence required for audit.
"""


class DRYDuplicationAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    classification: DRYDuplicationClassification
    is_exception: bool
    reasoning: str = Field(min_length=1)
    evidence: str = Field(min_length=1)
