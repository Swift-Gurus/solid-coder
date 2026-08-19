"""Defines normalized source content for deterministic analysis."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: ResolvedAnalysisSource
solid-category: model
solid-spec: [SPEC-040]
solid-description: Carries normalized source identity, exact extension, and content after boundary resolution.
"""
class ResolvedAnalysisSource(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    identity: str = Field(min_length=1)
    file_extension: str
    text: str
