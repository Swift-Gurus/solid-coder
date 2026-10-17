from typing import Protocol

from harness.flow_validation_error import FlowValidationError
from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_context_values import WorkflowContextValues
from review.normalized_review_unit import NormalizedReviewUnit
from source.source_unit_identity import SourceUnitIdentity


"""
solid-name: ReviewUnitSourceIdentityResolving
solid-category: abstraction
solid-description: Contract for deriving authoritative source-unit identity from normalized review inputs.
"""
class ReviewUnitSourceIdentityResolving(Protocol):
    def resolve(self, inputs: WorkflowContextValues[object]) -> SourceUnitIdentity | None: ...


"""
solid-name: ReviewUnitSourceIdentityResolver
solid-category: service
solid-spec: [SPEC-057]
solid-description: Resolves normalized review-unit provenance without claiming identities for unrelated custom inputs.
"""
class ReviewUnitSourceIdentityResolver(ReviewUnitSourceIdentityResolving):
    def __init__(self, decoder: StructuredModelDecoding[NormalizedReviewUnit]) -> None:
        self._decoder = decoder

    def resolve(self, inputs: WorkflowContextValues[object]) -> SourceUnitIdentity | None:
        value = inputs.find("review_unit")
        if not value.present:
            return None
        try:
            target = self._decoder.decode(value.value, "review unit provenance").target
        except FlowValidationError:
            return None
        return SourceUnitIdentity(
            source_identity=target.source_identity,
            unit_identity=target.unit_identity,
        )
