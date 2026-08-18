"""Defines the client-authored portion of one effective metric decision."""

from typing import Optional

from pydantic import BaseModel, ConfigDict

from harness.metric_scoring_declaration import MetricScoringDeclaration
from harness.project_review_policy_audit import ProjectReviewPolicyAudit


"""
solid-name: MetricPolicyOverrideAudit
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents client-authored metric override values, policy provenance, and audit reasoning.
"""
class MetricPolicyOverrideAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requested_enabled: Optional[bool] = None
    requested_scoring: Optional[MetricScoringDeclaration] = None
    policy: ProjectReviewPolicyAudit
    reason: Optional[str] = None
