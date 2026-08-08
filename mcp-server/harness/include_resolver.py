"""Expands workflow includes and inline groups recursively."""

from __future__ import annotations

from pathlib import Path

from harness.include_cycle_guarding import IncludeCycleGuarding
from harness.include_resolution import IncludeResolution
from harness.include_resolving import IncludeResolving
from harness.include_source import IncludeSource
from harness.include_source_resolving import IncludeSourceResolving
from harness.step_qualifying import StepQualifying


"""
solid-name: IncludeResolver
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Recursively expands selected include sources and aggregates alias and provenance results.
"""
class IncludeResolver(IncludeResolving):

    def __init__(
        self,
        source_resolver: IncludeSourceResolving,
        cycle_guard: IncludeCycleGuarding,
        step_qualifier: StepQualifying,
    ) -> None:
        self._source_resolver = source_resolver
        self._cycle_guard = cycle_guard
        self._step_qualifier = step_qualifier

    def resolve(
        self,
        raw_steps: list[dict],
        flow_file_path: str,
        search_paths: list[str] | None = None,
        root_workflow_id: str | None = None,
    ) -> IncludeResolution:
        root_path = str(Path(flow_file_path).resolve())
        return self._resolve(
            raw_steps,
            flow_file_path,
            search_paths or [],
            ancestor_identities=[root_path],
            ancestor_labels=[root_workflow_id or root_path],
        )

    def _resolve(
        self,
        raw_steps: list[dict],
        flow_file_path: str,
        search_paths: list[str],
        ancestor_identities: list[str],
        ancestor_labels: list[str],
    ) -> IncludeResolution:
        expanded_steps: list[dict] = []
        alias_groups: dict[str, list[str]] = {}
        include_chain = list(ancestor_labels)
        sources: list[str] = []
        workflow_ids: list[str] = []

        for entry in raw_steps:
            source = self._source_resolver.resolve(entry, flow_file_path, search_paths)
            if source is None:
                expanded_steps.append(entry)
                continue
            nested = self._expand_source(
                source,
                search_paths,
                ancestor_identities,
                ancestor_labels,
            )
            sibling_ids = {step["id"] for step in nested.steps}
            qualified_steps = [
                self._step_qualifier.qualify(step, source.alias, sibling_ids)
                for step in nested.steps
            ]
            expanded_steps.extend(qualified_steps)
            alias_groups[source.alias] = [step["id"] for step in qualified_steps]
            alias_groups.update(self._qualify_alias_groups(source.alias, nested.alias_groups))
            self._append_unique(include_chain, nested.include_chain)
            self._append_unique(sources, [source.source_path] if source.source_path else [])
            self._append_unique(sources, nested.sources)
            self._append_unique(workflow_ids, [source.workflow_id] if source.workflow_id else [])
            self._append_unique(workflow_ids, nested.workflow_ids)

        return IncludeResolution(
            steps=expanded_steps,
            alias_groups=alias_groups,
            include_chain=include_chain,
            sources=sources,
            workflow_ids=workflow_ids,
        )

    def _expand_source(
        self,
        source: IncludeSource,
        search_paths: list[str],
        ancestor_identities: list[str],
        ancestor_labels: list[str],
    ) -> IncludeResolution:
        self._cycle_guard.check(
            source.identity,
            source.label,
            ancestor_identities,
            ancestor_labels,
        )
        identities = ancestor_identities + ([source.identity] if source.identity else [])
        labels = ancestor_labels + ([source.label] if source.label else [])
        return self._resolve(
            source.steps,
            source.flow_path,
            search_paths,
            identities,
            labels,
        )

    def _qualify_alias_groups(
        self,
        alias: str,
        nested_groups: dict[str, list[str]],
    ) -> dict[str, list[str]]:
        return {
            f"{alias}.{nested_alias}": [f"{alias}.{member}" for member in members]
            for nested_alias, members in nested_groups.items()
        }

    def _append_unique(self, target: list[str], values: list[str]) -> None:
        for value in values:
            if value not in target:
                target.append(value)
