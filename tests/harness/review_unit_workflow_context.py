"""Defines the source-free review-unit shape used by direct rule-flow tests."""

from pydantic import BaseModel, ConfigDict

from review_unit_workflow_target import ReviewUnitWorkflowTarget


"""
solid-name: ReviewUnitWorkflowContext
solid-category: value
solid-spec: [SPEC-039]
solid-description: Mirrors the production review-unit target boundary while exposing only its model-facing name.
"""
class ReviewUnitWorkflowContext(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: ReviewUnitWorkflowTarget
