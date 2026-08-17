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
    sources: list[WorkflowSource]

    def find(self, workflow_id: str) -> WorkflowSource | None:
        return next(
            (source for source in self.sources if source.id == workflow_id),
            None,
        )

    def rule_sources(self) -> list[WorkflowSource]:
        return sorted(
            (source for source in self.sources if source.rule is not None),
            key=lambda source: source.id,
        )
