"""Applies project policy enablement to one enrolled review rule."""

from typing import cast

from harness.project_policy_rule_decision import ProjectPolicyRuleDecision
from harness.project_review_policy_audit import ProjectReviewPolicyAudit
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.rule_enablement_resolving import (
    RuleEnablementResolution,
    RuleEnablementResolving,
)
from harness.workflow_default_rule_decision import WorkflowDefaultRuleDecision


"""
solid-name: RuleEnablementResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Applies an authored project enablement request over the enabled workflow default with audit evidence.
"""
class RuleEnablementResolver(RuleEnablementResolving):
    def resolve(
        self,
        workflow_id: str,
        policy_resolution: ReviewPolicyResolution,
    ) -> RuleEnablementResolution:
        matches = [
            override
            for override in policy_resolution.policy.rules
            if override.workflow_id == workflow_id
        ]
        if not matches or matches[0].enabled is None:
            return WorkflowDefaultRuleDecision()
        override = matches[0]
        project_audit = cast(ProjectReviewPolicyAudit, policy_resolution.audit)
        return ProjectPolicyRuleDecision(
            client_requested=override.enabled,
            effective=override.enabled,
            policy=project_audit,
            reason=override.reason or "",
        )
