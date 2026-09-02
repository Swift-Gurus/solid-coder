"""Defines the model-visible target identity used by direct rule-flow tests."""

from pydantic import BaseModel, ConfigDict, Field


"""
solid-name: ReviewUnitWorkflowTarget
solid-category: value
solid-spec: [SPEC-039]
solid-description: Carries only the reviewed unit name into model-facing rule instructions while source remains MCP-owned.
"""
class ReviewUnitWorkflowTarget(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    name: str = Field(min_length=1)
