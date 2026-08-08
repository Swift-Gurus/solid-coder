"""Indexes workflow sources while enforcing global ID uniqueness."""

from __future__ import annotations

from harness.models import FlowValidationError
from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowSourceIndexer
solid-category: service
solid-spec: [SPEC-035]
solid-description: Indexes workflow sources by public ID and reports every duplicate source path.
"""
class WorkflowSourceIndexer:
    def index(self, sources: list[WorkflowSource]) -> dict[str, WorkflowSource]:
        grouped: dict[str, list[WorkflowSource]] = {}
        for source in sources:
            grouped.setdefault(source.id, []).append(source)

        conflicts = {workflow_id: matches for workflow_id, matches in grouped.items() if len(matches) > 1}
        if conflicts:
            details = "; ".join(
                f"'{workflow_id}': {', '.join(str(item.entry_path) for item in matches)}"
                for workflow_id, matches in sorted(conflicts.items())
            )
            raise FlowValidationError(f"Duplicate workflow IDs detected: {details}")

        return {workflow_id: matches[0] for workflow_id, matches in grouped.items()}
