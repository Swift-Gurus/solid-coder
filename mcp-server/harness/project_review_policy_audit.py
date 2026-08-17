"""Identifies the project policy source preserved by an effective plan."""

from pathlib import Path
from typing import Literal

from harness.review_policy_audit import ReviewPolicyAudit


"""
solid-name: ProjectReviewPolicyAudit
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records project review-policy provenance preserved by an effective review-rule plan.
"""
class ProjectReviewPolicyAudit(ReviewPolicyAudit):
    source: Literal["project"] = "project"
    source_path: Path
    content_hash: str
