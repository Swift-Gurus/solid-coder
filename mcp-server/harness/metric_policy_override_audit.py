"""Defines the client-authored portion of one effective metric decision."""

from harness.metric_scoring_declaration import MetricScoringDeclaration
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from pydantic import BaseModel, ConfigDict

"""
solid-name: MetricPolicyOverrideAudit
solid-category: model
solid-spec: [SPEC-039]
solid-description: Represents client-authored metric override values, policy provenance, and audit reasoning.
"""


class MetricPolicyOverrideAudit(BaseModel):
    model_config = ConfigDict(extra="forbid", frozen=True)

    requested_enabled: bool | None = None
    requested_scoring: MetricScoringDeclaration | None = None
    policy: ProjectReviewPolicyAudit
    reason: str | None = None
