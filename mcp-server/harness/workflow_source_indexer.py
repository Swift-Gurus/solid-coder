"""Indexes workflow sources while enforcing global ID uniqueness."""

from __future__ import annotations

from harness.models import FlowValidationError
from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowSourceIndexer
solid-category: service
solid-spec: [SPEC-035]
solid-description: Orders workflow sources by public ID and reports every duplicate source path.
"""
class WorkflowSourceIndexer:
    def index(self, sources: list[WorkflowSource]) -> list[WorkflowSource]:
        sources_by_path = sorted(sources, key=lambda source: str(source.entry_path))
        ordered_sources = sorted(sources_by_path, key=lambda source: source.id)
        groups: list[list[WorkflowSource]] = []
        for source in ordered_sources:
            if groups and groups[-1][0].id == source.id:
                groups[-1].append(source)
            else:
                groups.append([source])

        conflicts = [group for group in groups if len(group) > 1]
        if conflicts:
            details = "; ".join(
                f"'{group[0].id}': {', '.join(str(item.entry_path) for item in group)}"
                for group in conflicts
            )
            raise FlowValidationError(f"Duplicate workflow IDs detected: {details}")

        return ordered_sources
