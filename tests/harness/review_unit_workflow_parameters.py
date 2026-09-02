"""Defines typed parameters for directly exercising one review-rule workflow."""

from pydantic import BaseModel, ConfigDict

from review_unit_workflow_context import ReviewUnitWorkflowContext


"""
solid-name: ReviewUnitWorkflowParameters
solid-category: value
solid-spec: [SPEC-039]
solid-description: Carries one normalized source unit into a directly invoked executable review-rule workflow.
"""
class ReviewUnitWorkflowParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    review_unit: ReviewUnitWorkflowContext
    repository_evidence: str = "No MCP-owned repository evidence was supplied."
