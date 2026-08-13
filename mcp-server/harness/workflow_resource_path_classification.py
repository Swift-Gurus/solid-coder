"""Defines a classified workflow resource path."""

from dataclasses import dataclass
from pathlib import Path

from harness.workflow_resource_reference_kind import WorkflowResourceReferenceKind


"""
solid-name: WorkflowResourcePathClassification
solid-category: model
solid-spec: [SPEC-035]
solid-description: Identifies a workflow resource path and the anchor used to resolve it.
"""
@dataclass(frozen=True)
class WorkflowResourcePathClassification:
    path: Path
    kind: WorkflowResourceReferenceKind
