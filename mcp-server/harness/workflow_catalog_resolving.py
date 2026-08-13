"""Defines workflow catalog lookup."""

from __future__ import annotations

from contextlib import AbstractContextManager
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


"""
solid-name: WorkflowCatalogScoping
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for sharing one workflow catalog during a single flow-definition load.
"""
class WorkflowCatalogScoping(Protocol):
    def scope(self, search_paths: list[str]) -> AbstractContextManager[None]: ...
