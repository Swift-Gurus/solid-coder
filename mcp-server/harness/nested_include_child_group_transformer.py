"""Coordinates nested child-group transformation."""

from harness.combined_rule_presentation_creating import (
    CombinedRulePresentationCreating,
)
from harness.include_alias_group import IncludeAliasGroup
from harness.include_alias_group_replacing import IncludeAliasGroupReplacing
from harness.include_source import IncludeSource
from harness.nested_include_child_group_policy_selecting import (
    NestedIncludeChildGroupPolicySelecting,
)
from harness.nested_include_child_group_transforming import (
    NestedIncludeChildGroupTransforming,
)


"""
solid-name: NestedIncludeChildGroupTransformer
solid-category: service
solid-spec: [SPEC-027, SPEC-035, SPEC-045]
solid-description: Coordinates policy selection and replacement for one nested child group.
"""
class NestedIncludeChildGroupTransformer(NestedIncludeChildGroupTransforming):
    def __init__(
        self,
        policy_selector: NestedIncludeChildGroupPolicySelecting,
        presentation_factory: CombinedRulePresentationCreating,
        group_replacer: IncludeAliasGroupReplacing,
    ) -> None:
        self._policy_selector = policy_selector
        self._presentation_factory = presentation_factory
        self._group_replacer = group_replacer

    def transform(
        self,
        group: IncludeAliasGroup,
        source: IncludeSource,
        transparent_aliases: set[str],
    ) -> IncludeAliasGroup:
        policy = self._policy_selector.select(
            group,
            source,
            transparent_aliases,
        )
        if policy is None:
            return group
        presentation = group.combined_presentation
        if policy.combines_presentation:
            presentation = self._presentation_factory.create(
                source.alias,
                group.authored_alias,
            )
        return self._group_replacer.replace_policy(
            group,
            policy,
            presentation,
        )
