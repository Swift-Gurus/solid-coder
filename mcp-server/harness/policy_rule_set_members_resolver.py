"""Applies project review-policy enablement to rules-all members."""

from harness.review_policy_loading import ReviewPolicyLoading
from harness.rule_enablement_resolving import RuleEnablementResolving
from harness.rule_set_member_include import RuleSetMemberInclude
from harness.rule_set_members_resolving import RuleSetMembersResolving
from harness.workflow_include_runtime import WorkflowIncludeRuntime


"""
solid-name: PolicyRuleSetMembersResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Filters catalog rule members through the effective project-policy enablement decision before materialization.
"""
class PolicyRuleSetMembersResolver(RuleSetMembersResolving):

    def __init__(
        self,
        members: RuleSetMembersResolving,
        policy_loader: ReviewPolicyLoading,
        enablement: RuleEnablementResolving,
    ) -> None:
        self._members = members
        self._policy_loader = policy_loader
        self._enablement = enablement

    def resolve(
        self,
        search_paths: list[str],
        runtime: WorkflowIncludeRuntime,
    ) -> list[RuleSetMemberInclude]:
        policy = self._policy_loader.load()
        return [
            member
            for member in self._members.resolve(search_paths, runtime)
            if self._enablement.resolve(
                member.workflow_id,
                policy,
            ).effective
        ]
