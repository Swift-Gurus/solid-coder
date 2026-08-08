"""Defines the workflow catalog construction boundary."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.workflow_catalog import WorkflowCatalog


"""
solid-name: WorkflowCatalogBuilding
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for constructing a workflow catalog from client and plugin roots.
"""
class WorkflowCatalogBuilding(Protocol):
    def build(self, roots: list[Path]) -> WorkflowCatalog: ...
