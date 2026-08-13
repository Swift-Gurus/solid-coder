"""Defines workflow resource path resolution."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol

from harness.workflow_resource_reference import WorkflowResourceReference


"""
solid-name: WorkflowResourcePathResolving
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for resolving package-contained paths declared by workflow YAML files.
"""
class WorkflowResourcePathResolving(Protocol):
    def resolve(
        self,
        declaring_file: Path,
        reference: WorkflowResourceReference,
    ) -> Path: ...
