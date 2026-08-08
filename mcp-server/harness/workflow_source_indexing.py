"""Defines unique indexing of discovered workflow sources."""

from __future__ import annotations

from typing import Protocol

from harness.workflow_source import WorkflowSource


"""
solid-name: WorkflowSourceIndexing
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for collision-checked indexing of workflow sources by public ID.
"""
class WorkflowSourceIndexing(Protocol):
    def index(self, sources: list[WorkflowSource]) -> dict[str, WorkflowSource]: ...
