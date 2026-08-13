"""Merges qualified nested includes into aggregate resolutions."""

from dataclasses import replace

from harness.include_alias_group_creating import IncludeAliasGroupCreating
from harness.include_resolution import IncludeResolution
from harness.include_source import IncludeSource
from harness.nested_include_resolution_merging import NestedIncludeResolutionMerging
from harness.ordered_string_collecting import OrderedStringCollecting


"""
solid-name: NestedIncludeResolutionMerger
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Merges a qualified nested include into an aggregate resolution.
"""
class NestedIncludeResolutionMerger(NestedIncludeResolutionMerging):

    def __init__(
        self,
        alias_group_factory: IncludeAliasGroupCreating,
        ordered_strings: OrderedStringCollecting,
    ) -> None:
        self._alias_group_factory = alias_group_factory
        self._ordered_strings = ordered_strings

    def merge(
        self,
        resolution: IncludeResolution,
        source: IncludeSource,
        nested: IncludeResolution,
    ) -> IncludeResolution:
        source_group = self._alias_group_factory.create(
            alias=source.alias,
            member_ids=[step["id"] for step in nested.steps],
        )
        alias_groups = [
            group
            for group in resolution.alias_groups
            if group.alias != source.alias
        ]
        alias_groups.extend([source_group, *nested.alias_groups])
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
