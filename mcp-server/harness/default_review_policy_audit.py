"""Identifies an effective plan without a project-authored policy."""

from typing import Literal

from harness.review_policy_audit import ReviewPolicyAudit


"""
solid-name: DefaultReviewPolicyAudit
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records that an effective review-rule plan uses workflow defaults without project policy input.
"""
class DefaultReviewPolicyAudit(ReviewPolicyAudit):
    source: Literal["default"] = "default"
