"""Plans all enrolled catalog rules as typed include members."""

from harness.enrolled_rule_sources_selector import EnrolledRuleSourcesSelecting
from harness.rule_set_member_include import RuleSetMemberInclude
from harness.rule_set_member_resolver import RuleSetMemberResolving
from harness.rule_set_members_resolving import RuleSetMembersResolving
from harness.workflow_include_runtime import WorkflowIncludeRuntime

"""
solid-name: CatalogRuleSetMembersResolver
solid-category: service
solid-spec: [SPEC-039]
solid-description: Resolves enrolled rules from one scoped catalog into stable conditioned include members.
"""


class CatalogRuleSetMembersResolver(RuleSetMembersResolving):
    def __init__(
        self,
        source_selector: EnrolledRuleSourcesSelecting,
        member_resolver: RuleSetMemberResolving,
    ) -> None:
        self._source_selector = source_selector
        self._member_resolver = member_resolver

    def resolve(
        self,
        search_paths: list[str],
        runtime: WorkflowIncludeRuntime,
    ) -> list[RuleSetMemberInclude]:
        return [
            self._member_resolver.resolve(source, runtime)
            for source in self._source_selector.select(search_paths)
        ]
