"""Recursively traverses workflow include sources."""

from harness.include_resolution import IncludeResolution
from harness.include_resolution_merging import IncludeResolutionMerging
from harness.include_source_expansion_preparing import IncludeSourceExpansionPreparing
from harness.include_source_resolving import IncludeSourceResolving
from harness.include_traversal_context import IncludeTraversalContext
from harness.include_traversing import IncludeTraversing
from harness.nested_include_qualifying import NestedIncludeQualifying


"""
solid-name: IncludeTraverser
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Recursively traverses and expands workflow include sources.
"""
class IncludeTraverser(IncludeTraversing):

    def __init__(
        self,
        source_resolver: IncludeSourceResolving,
        expansion_preparer: IncludeSourceExpansionPreparing,
        nested_qualifier: NestedIncludeQualifying,
        resolution_merger: IncludeResolutionMerging,
    ) -> None:
        self._source_resolver = source_resolver
        self._expansion_preparer = expansion_preparer
        self._nested_qualifier = nested_qualifier
        self._resolution_merger = resolution_merger

    def traverse(
        self,
        raw_steps: list[dict],
        search_paths: list[str],
        context: IncludeTraversalContext,
    ) -> IncludeResolution:
        resolution = IncludeResolution(
            include_chain=list(context.ancestor_labels),
        )
        for entry in raw_steps:
            source = self._source_resolver.resolve(
                entry,
                context.flow_file_path,
                search_paths,
            )
            if source is None:
                resolution = self._resolution_merger.append_step(resolution, entry)
                continue
            nested_context = self._expansion_preparer.prepare(source, context)
            nested = self.traverse(source.steps, search_paths, nested_context)
            qualified = self._nested_qualifier.qualify(source.alias, nested)
            resolution = self._resolution_merger.merge(
                resolution,
                source,
                qualified,
            )
        return resolution
