"""Defines planning of typed members for an all-rules include."""

from typing import Protocol

from harness.rule_set_member_include import RuleSetMemberInclude
from harness.workflow_include_runtime import WorkflowIncludeRuntime


"""
solid-name: RuleSetMembersResolving
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for resolving ordered catalog rules into typed rule-set members.
"""
class RuleSetMembersResolving(Protocol):
    def resolve(
        self,
        search_paths: list[str],
        runtime: WorkflowIncludeRuntime,
    ) -> list[RuleSetMemberInclude]: ...
