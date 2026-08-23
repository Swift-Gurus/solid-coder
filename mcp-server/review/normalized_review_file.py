"""Defines one normalized file supplied to file review."""

from pydantic import BaseModel, ConfigDict, Field

from harness.rule_applicability_context import RuleApplicabilityContext
from source.source_search_target import SourceSearchTarget
from source.technology_detection import TechnologyDetection


"""
solid-name: NormalizedReviewFile
solid-category: model
solid-spec: [SPEC-039, SPEC-041]
solid-description: Represents one normalized immutable review-file target.
"""
class NormalizedReviewFile(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: SourceSearchTarget
    applicability: RuleApplicabilityContext
    tag_evidence: list[TechnologyDetection] = Field(default_factory=list)
