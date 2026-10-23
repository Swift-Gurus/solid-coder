"""Defines one schema-validated live DRY candidate assessment."""

from dry_duplication_assessment import DRYDuplicationAssessment
from dry_reuse_assessment import DRYReuseAssessment
from pydantic import BaseModel, ConfigDict, Field

"""
solid-name: DRYCandidateAssessment
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Maps one candidate output into independent reuse and implementation-duplication decisions.
"""


class DRYCandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    candidate_id: str = Field(pattern=r"^candidate-[1-9][0-9]*$")
    location: str = Field(min_length=1)
    reuse: DRYReuseAssessment
    duplication: DRYDuplicationAssessment
