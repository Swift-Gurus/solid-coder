"""Defines optional metadata that enrolls a workflow as a review rule."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: RuleDeclaration
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries a review rule's optional reporting category and required applicability tags.
"""
class RuleDeclaration(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    category: Optional[str] = None
    tags: list[str] = Field(default_factory=list)
