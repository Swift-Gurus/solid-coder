"""Represents a resolved project-authored review policy and its audit source."""

from typing import Literal

from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.review_policy_resolution import ReviewPolicyResolution


"""
solid-name: ProjectReviewPolicyResolution
solid-category: model
solid-spec: [SPEC-039]
solid-description: Resolves project-authored review policy state with its auditable source and content hash.
"""
class ProjectReviewPolicyResolution(ReviewPolicyResolution):
    source: Literal["project"] = "project"
    audit: ProjectReviewPolicyAudit
