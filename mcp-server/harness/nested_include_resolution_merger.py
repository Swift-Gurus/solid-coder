"""Merges qualified nested includes into aggregate resolutions."""

from dataclasses import replace

from harness.combined_rule_presentation import CombinedRulePresentation
from harness.include_alias_group import IncludeAliasGroup
from harness.include_resolution import IncludeResolution
from harness.include_source import IncludeSource
from harness.include_group_dynamic_checking import IncludeGroupDynamicChecking
from harness.nested_include_resolution_merging import NestedIncludeResolutionMerging
from harness.ordered_string_collecting import OrderedStringCollecting
from harness.workflow_presentation_mode import WorkflowPresentationMode


"""
solid-name: NestedIncludeResolutionMerger
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Merges a qualified nested include into an aggregate resolution.
"""
class NestedIncludeResolutionMerger(NestedIncludeResolutionMerging):

    def __init__(
        self,
        ordered_strings: OrderedStringCollecting,
        dynamic_group_checker: IncludeGroupDynamicChecking,
    ) -> None:
        self._ordered_strings = ordered_strings
        self._dynamic_group_checker = dynamic_group_checker

    def merge(
        self,
        resolution: IncludeResolution,
        source: IncludeSource,
        nested: IncludeResolution,
    ) -> IncludeResolution:
        transparent_aliases = {
            group.alias
            for group in nested.alias_groups
            if group.owner_alias is None
            and not self._dynamic_group_checker.is_dynamic(group)
        }
        owned_groups = [
            self._merge_child_group(group, source, transparent_aliases)
            for group in nested.alias_groups
        ]
        owned_member_ids = {
            member_id
            for group in owned_groups
            for member_id in group.member_ids
        }
        source_group = IncludeAliasGroup(
            alias=source.alias,
            member_ids=[
                step["id"]
                for step in nested.steps
                if step["id"] not in owned_member_ids
            ],
            depends_on=source.runtime.depends_on,
            for_each=source.runtime.for_each,
            input_bindings=source.runtime.input_bindings,
            condition=source.runtime.condition,
            rule_workflow=source.rule_workflow,
            outputs=source.outputs,
        )
        alias_groups = [
            group
            for group in resolution.alias_groups
            if group.alias != source.alias
        ]
        alias_groups.extend([source_group, *owned_groups])
        source_paths = [source.source_path] if source.source_path else []
        workflow_ids = [source.workflow_id] if source.workflow_id else []
        return replace(
            resolution,
            steps=[*resolution.steps, *nested.steps],
            alias_groups=alias_groups,
            include_chain=self._ordered_strings.collect(
                [resolution.include_chain, nested.include_chain]
            ),
            sources=self._ordered_strings.collect(
                [resolution.sources, source_paths, nested.sources]
            ),
            workflow_ids=self._ordered_strings.collect(
                [resolution.workflow_ids, workflow_ids, nested.workflow_ids]
            ),
        )

    def _merge_child_group(
        self,
        group: IncludeAliasGroup,
        source: IncludeSource,
        transparent_aliases: set[str],
    ) -> IncludeAliasGroup:
        owns_group = (
            group.owner_alias is None
            and self._dynamic_group_checker.is_dynamic(group)
        ) or group.owner_alias in transparent_aliases
        presents_group = (
            group.owner_alias is None
            and source.runtime.presentation is WorkflowPresentationMode.COMBINED
        )
        if not owns_group and not presents_group:
            return group
        return replace(
            group,
            owner_alias=source.alias if owns_group else group.owner_alias,
            combined_presentation=(
                CombinedRulePresentation(
                    group_alias=source.alias,
                    rule_alias=group.authored_alias,
                )
                if presents_group or owns_group
                and source.runtime.presentation is WorkflowPresentationMode.COMBINED
                else group.combined_presentation
            ),
        )
