"""Defines one schema-validated live DRY candidate assessment."""

from pydantic import BaseModel, ConfigDict

from dry_duplication_assessment import DRYDuplicationAssessment
from dry_reuse_assessment import DRYReuseAssessment


"""
solid-name: DRYCandidateAssessment
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Maps one candidate output into independent reuse and implementation-duplication decisions.
"""
class DRYCandidateAssessment(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    reuse: DRYReuseAssessment
    duplication: DRYDuplicationAssessment
