"""Defines workflow catalog lookup."""

from __future__ import annotations

from typing import Protocol

from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowCatalogResolving
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for resolving workflow IDs across a combined client and plugin catalog.
"""
class WorkflowCatalogResolving(Protocol):
    def resolve(self, workflow_id: str, search_paths: list[str]) -> WorkflowSource | None: ...
