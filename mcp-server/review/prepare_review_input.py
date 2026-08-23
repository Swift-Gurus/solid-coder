"""Defines the typed input to review-target normalization."""

from pydantic import BaseModel, ConfigDict

from review.buffer_review_target import BufferReviewTarget


"""
solid-name: PrepareReviewInput
solid-category: model
solid-spec: [SPEC-041]
solid-description: Selects the explicit target normalized before review-rule materialization.
"""
class PrepareReviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    target: BufferReviewTarget
