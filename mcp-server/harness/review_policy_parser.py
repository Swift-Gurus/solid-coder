"""Coordinates typed decoding and identity validation of client review policy input."""

from harness.review_policy import ReviewPolicy
from harness.review_policy_validating import ReviewPolicyValidating
from harness.structured_model_decoding import StructuredModelDecoding


"""
solid-name: ReviewPolicyParser
solid-category: service
solid-spec: [SPEC-039]
solid-description: Coordinates shared structured decoding and workflow-identity validation for client review policy input.
"""
class ReviewPolicyParser:

    def __init__(
        self,
        decoder: StructuredModelDecoding[ReviewPolicy],
        validators: list[ReviewPolicyValidating],
    ) -> None:
        self._decoder = decoder
        self._validators = validators

    def parse(self, value: object) -> ReviewPolicy:
        policy = self._decoder.decode(value, "review policy")
        for validator in self._validators:
            validator.validate(policy)
        return policy
