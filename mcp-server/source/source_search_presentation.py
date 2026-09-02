"""Defines readable workflow-facing source-search output."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: SourceSearchPresentation
solid-category: model
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries the readable source-search summary supplied to a workflow step.
"""
class SourceSearchPresentation(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    text: str = Field(min_length=1)
