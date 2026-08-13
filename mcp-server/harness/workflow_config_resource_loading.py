"""Defines structured workflow-resource loading."""

from __future__ import annotations

from pathlib import Path
from typing import Optional, Protocol

from harness.workflow_config_resource import WorkflowConfigResource
from harness.workflow_resource_reference import WorkflowResourceReference


"""
solid-name: WorkflowConfigResourceLoading
solid-category: abstraction
solid-spec: [SPEC-035]
solid-description: Contract for resolving and loading optional structured workflow resources.
"""
class WorkflowConfigResourceLoading(Protocol):
    def load(
        self,
        declaring_file: Path,
        reference: WorkflowResourceReference,
    ) -> Optional[WorkflowConfigResource]: ...
