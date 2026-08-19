"""Defines normalized file and unit facts used for review-rule matching."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind


"""
solid-name: RuleApplicabilityContext
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries exact extension, unit kind, and MCP-owned tags for rule matching.
"""
class RuleApplicabilityContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file_extension: str
    unit_kind: ReviewUnitKind
    tags: list[str] = Field(default_factory=list)
