"""Defines effective enablement resolution for one review rule."""

from typing import Protocol, Union

from harness.project_policy_rule_decision import ProjectPolicyRuleDecision
from harness.review_policy_resolution import ReviewPolicyResolution
from harness.workflow_default_rule_decision import WorkflowDefaultRuleDecision

RuleEnablementResolution = Union[
    WorkflowDefaultRuleDecision,
    ProjectPolicyRuleDecision,
]


"""
solid-name: RuleEnablementResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for applying project review-policy enablement over one workflow default.
"""
class RuleEnablementResolving(Protocol):
    def resolve(
        self,
        workflow_id: str,
        policy_resolution: ReviewPolicyResolution,
    ) -> RuleEnablementResolution: ...
