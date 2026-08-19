"""Defines reusable included/excluded values for review-rule matching."""

from __future__ import annotations

from typing import Generic, TypeVar

from pydantic import BaseModel, ConfigDict, Field


SelectionValue = TypeVar("SelectionValue")


"""
solid-name: RuleSelection
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries optional included and excluded values for one rule matcher dimension.
"""
class RuleSelection(BaseModel, Generic[SelectionValue]):
    model_config = ConfigDict(extra="forbid", frozen=True)

    included: list[SelectionValue] = Field(default_factory=list)
    excluded: list[SelectionValue] = Field(default_factory=list)
