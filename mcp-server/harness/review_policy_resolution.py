"""Defines the common typed result of resolving review policy state."""

from harness.default_review_policy_audit import DefaultReviewPolicyAudit
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.review_policy import ReviewPolicy
from pydantic import BaseModel, ConfigDict

"""
solid-name: ReviewPolicyResolution
solid-category: model
solid-spec: [SPEC-039]
solid-description: Carries the effective typed review policy shared by absent and project-authored resolution outcomes.
"""


class ReviewPolicyResolution(BaseModel):
    model_config = ConfigDict(frozen=True)

    policy: ReviewPolicy
    audit: DefaultReviewPolicyAudit | ProjectReviewPolicyAudit
    authored_content: str = ""
