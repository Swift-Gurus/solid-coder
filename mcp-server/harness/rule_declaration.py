"""Defines optional metadata that enrolls a workflow as a review rule."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field, StrictBool

from harness.rule_match_declaration import RuleMatchDeclaration
from harness.rule_exception_decision import RuleExceptionDecision
from harness.rule_scope import RuleScope


"""
solid-name: RuleDeclaration
solid-category: model
solid-spec: [SPEC-039, SPEC-066]
solid-description: Carries a review rule's execution scope, typed applicability matcher, and optional authored exception decision.
"""
class RuleDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    auto_include: StrictBool = True
    scope: RuleScope = RuleScope.UNIT
    match: RuleMatchDeclaration = Field(default_factory=RuleMatchDeclaration)
    exception: RuleExceptionDecision | None = None
