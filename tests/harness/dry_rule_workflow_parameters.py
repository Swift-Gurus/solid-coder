"""Defines typed parameters for directly exercising the unit-scoped DRY workflow."""

from pydantic import BaseModel, ConfigDict

from review.normalized_review_unit import NormalizedReviewUnit
from source.source_search_context import SourceSearchContext


"""
solid-name: DRYRuleWorkflowParameters
solid-category: value
solid-spec: [SPEC-039, SPEC-040]
solid-description: Carries one immutable review unit and its authoritative prospective source context into DRY validation.
"""
class DRYRuleWorkflowParameters(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    review_unit: NormalizedReviewUnit
    source_context: SourceSearchContext
