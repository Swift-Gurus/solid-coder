"""Resolves and loads structured workflow resources."""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from harness.workflow_config_resource import WorkflowConfigResource
from harness.workflow_resource_reference import WorkflowResourceReference
from harness.workflow_resource_path_resolving import WorkflowResourcePathResolving
from scoring.yaml_config_file_loader import ConfigFileLoading


"""
solid-name: WorkflowConfigResourceLoader
solid-category: service
solid-spec: [SPEC-035]
solid-description: Loads optional structured workflow content through the shared resource-path policy.
"""
class WorkflowConfigResourceLoader:

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        path_resolver: WorkflowResourcePathResolving,
    ) -> None:
        self._file_loader = file_loader
        self._path_resolver = path_resolver

    def load(
        self,
        declaring_file: Path,
        reference: WorkflowResourceReference,
    ) -> Optional[WorkflowConfigResource]:
        path = self._path_resolver.resolve(declaring_file, reference)
        content = self._file_loader.load(path)
        if content is None:
            return None
        return WorkflowConfigResource(path=path, content=content)
