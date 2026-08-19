"""Plans all enrolled catalog rules as typed include members."""

from dataclasses import replace

from harness.condition_conjoining import ConditionConjoining
from harness.rule_match_condition_compiling import RuleMatchConditionCompiling
from harness.rule_set_member_include import RuleSetMemberInclude
from harness.rule_set_members_resolving import RuleSetMembersResolving
from harness.workflow_catalog_resolving import WorkflowCatalogResolving
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
        catalog_resolver: WorkflowCatalogResolving,
        match_compiler: RuleMatchConditionCompiling,
        condition_conjoiner: ConditionConjoining,
    ) -> None:
        self._catalog_resolver = catalog_resolver
        self._match_compiler = match_compiler
        self._condition_conjoiner = condition_conjoiner

    def resolve(
        self,
        search_paths: list[str],
        runtime: WorkflowIncludeRuntime,
    ) -> list[RuleSetMemberInclude]:
        member_runtime = replace(runtime, condition=None)
        return [
            RuleSetMemberInclude(
                workflow_id=source.id,
                alias=source.id,
                runtime=member_runtime,
                condition=self._condition_conjoiner.conjoin([
                    runtime.condition,
                    self._match_compiler.compile(source.rule.match),
                ]),
            )
            for source in self._catalog_resolver.catalog(
                search_paths
            ).rule_sources()
            if source.rule is not None
        ]
