"""Defines optional metadata that enrolls a workflow as a review rule."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field

from harness.rule_match_declaration import RuleMatchDeclaration


"""
solid-name: RuleDeclaration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries a review rule's reporting category and typed applicability matcher.
"""
class RuleDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: Optional[str] = None
    match: RuleMatchDeclaration = Field(default_factory=RuleMatchDeclaration)
