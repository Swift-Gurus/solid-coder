"""Defines immutable lookup of discovered workflow sources."""

from __future__ import annotations

from dataclasses import dataclass

from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowCatalog
solid-category: model
solid-spec: [SPEC-035]
solid-description: Provides immutable lookup of uniquely identified workflow sources.
"""
@dataclass(frozen=True)
class WorkflowCatalog:
    sources: dict[str, WorkflowSource]

    def find(self, workflow_id: str) -> WorkflowSource | None:
        return self.sources.get(workflow_id)
