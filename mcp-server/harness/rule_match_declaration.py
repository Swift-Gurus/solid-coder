"""Defines typed applicability dimensions for one executable review rule."""

from pydantic import BaseModel, ConfigDict, Field

from findings.review_unit_kind import ReviewUnitKind
from harness.rule_selection import RuleSelection


"""
solid-name: RuleMatchDeclaration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries file-extension, unit-kind, and tag selectors for one review rule.
"""
class RuleMatchDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    file_extensions: RuleSelection[str] = Field(
        default_factory=lambda: RuleSelection[str]()
    )
    unit_kinds: RuleSelection[ReviewUnitKind] = Field(
        default_factory=lambda: RuleSelection[ReviewUnitKind]()
    )
    tags: RuleSelection[str] = Field(
        default_factory=lambda: RuleSelection[str]()
    )
