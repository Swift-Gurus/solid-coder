"""Defines a parsed workflow resource reference."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from harness.workflow_resource_directory import WorkflowResourceDirectory
from harness.workflow_resource_reference_kind import WorkflowResourceReferenceKind


"""
solid-name: WorkflowResourceReference
solid-category: model
solid-spec: [SPEC-035]
solid-description: Identifies a workflow resource path, its resolution anchor, and its conventional package directory.
"""
@dataclass(frozen=True)
class WorkflowResourceReference:
    declared_value: str
    path: Path
    kind: WorkflowResourceReferenceKind
    conventional_directory: WorkflowResourceDirectory
