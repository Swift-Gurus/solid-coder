"""Defines the normalized collection consumed by review workflows."""

from pydantic import BaseModel, ConfigDict, Field

from review.normalized_review_file import NormalizedReviewFile
from review.normalized_review_unit import NormalizedReviewUnit
from source.source_search_context import SourceSearchContext


"""
solid-name: NormalizedReviewInput
solid-category: model
solid-spec: [SPEC-041]
solid-description: Defines one normalized file, its ordered units, and source context required by the buffer review slice.
"""
class NormalizedReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    review_file: NormalizedReviewFile
    units: list[NormalizedReviewUnit] = Field(default_factory=list)
    source_context: SourceSearchContext
