"""Defines direct-test inputs for the ISP rule workflow."""

from pydantic import BaseModel, ConfigDict

from review.normalized_review_unit import NormalizedReviewUnit
from source.source_search_context import SourceSearchContext


"""
solid-name: ISPRuleWorkflowParameters
solid-category: test-support
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries one normalized protocol and authoritative source snapshot into a directly invoked ISP workflow.
"""
class ISPRuleWorkflowParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    review_unit: NormalizedReviewUnit
    source_context: SourceSearchContext
