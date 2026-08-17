"""Defines semantic validation of a decoded client review policy."""

from typing import Protocol

from harness.review_policy import ReviewPolicy


"""
solid-name: ReviewPolicyValidating
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for validating semantic invariants of typed client review policy records.
"""
class ReviewPolicyValidating(Protocol):

    def validate(self, policy: ReviewPolicy) -> None:
        ...
