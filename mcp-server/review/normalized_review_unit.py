"""Defines one normalized unit supplied to review rules."""

from pydantic import BaseModel, ConfigDict, Field

from harness.rule_applicability_context import RuleApplicabilityContext
from source.source_search_target import SourceSearchTarget
from source.technology_detection import TechnologyDetection


"""
solid-name: NormalizedReviewUnit
solid-category: model
solid-spec: [SPEC-039, SPEC-041]
solid-description: Carries exact unit source, deterministic applicability, and auditable tag evidence into rule workflows.
"""
class NormalizedReviewUnit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: SourceSearchTarget
    applicability: RuleApplicabilityContext
    tag_evidence: list[TechnologyDetection] = Field(default_factory=list)
