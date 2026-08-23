"""Composes internal review-domain workflow operations."""

from harness.operation_registration import OperationRegistration
from review.normalized_review_input import NormalizedReviewInput
from review.prepare_review_input import PrepareReviewInput
from review.prepare_review_operation_factory import PrepareReviewOperationFactory


"""
solid-name: ReviewOperationRegistrationsFactory
solid-category: factory
solid-spec: [SPEC-036, SPEC-041]
solid-description: Provides typed review-target preparation to the flow engine without exposing transport-specific tools.
"""
class ReviewOperationRegistrationsFactory:
    def make(self) -> list[OperationRegistration]:
        return [
            OperationRegistration(
                name="review.prepare",
                input_model=PrepareReviewInput,
                output_model=NormalizedReviewInput,
                handler=PrepareReviewOperationFactory().make(),
            )
        ]
