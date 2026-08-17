"""Represents rule enablement selected by the project review policy."""

from typing import Literal

from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.rule_enablement_decision import RuleEnablementDecision


"""
solid-name: ProjectPolicyRuleDecision
solid-category: model
solid-spec: [SPEC-039]
solid-description: Records project-requested review-rule enablement and the audit evidence proving its precedence.
"""
class ProjectPolicyRuleDecision(RuleEnablementDecision):
    source: Literal["project_policy"] = "project_policy"
    client_requested: bool
    policy: ProjectReviewPolicyAudit
    reason: str = ""
