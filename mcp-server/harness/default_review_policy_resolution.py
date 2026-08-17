"""Represents review policy resolution when a project policy is absent."""

from typing import Literal

from pydantic import Field

from harness.default_review_policy_audit import DefaultReviewPolicyAudit
from harness.review_policy import ReviewPolicy
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: DefaultReviewPolicyResolution
solid-category: model
solid-spec: [SPEC-039]
solid-description: Resolves default review policy state when no project-authored policy exists.
"""
class DefaultReviewPolicyResolution(ReviewPolicyResolution):
    source: Literal["default"] = "default"
    policy: ReviewPolicy = Field(default_factory=lambda: ReviewPolicy(version=1))
    audit: DefaultReviewPolicyAudit = Field(
        default_factory=DefaultReviewPolicyAudit
    )
