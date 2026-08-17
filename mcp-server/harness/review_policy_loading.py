"""Defines loading of resolved project review-policy state."""

from typing import Protocol

from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: ReviewPolicyLoading
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for loading normalized review-policy state from the active project boundary.
"""
class ReviewPolicyLoading(Protocol):
    def load(self) -> ReviewPolicyResolution: ...
