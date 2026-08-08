"""Discovers workflow sources without deciding collision policy."""

from __future__ import annotations

from pathlib import Path

from harness.workflow_package_validating import WorkflowPackageValidating
from harness.workflow_source import WorkflowSource
from scoring.yaml_config_file_loader import ConfigFileLoading

_ENTRYPOINT = "workflow.yaml"


"""
solid-name: WorkflowSourceDiscoverer
solid-category: service
solid-spec: [SPEC-035]
solid-description: Discovers package entrypoints recursively and direct legacy YAML flows below one root.
"""
class WorkflowSourceDiscoverer:

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        package_validator: WorkflowPackageValidating,
    ) -> None:
        self._file_loader = file_loader
        self._package_validator = package_validator

    def discover(self, root: Path) -> list[WorkflowSource]:
        if not root.is_dir():
            return []
        return self._packages(root) + self._legacy_flows(root)

    def _packages(self, root: Path) -> list[WorkflowSource]:
        sources: list[WorkflowSource] = []
        for entry_path in sorted(root.rglob(_ENTRYPOINT)):
            raw = self._file_loader.load(entry_path)
            self._package_validator.validate(entry_path, raw)
            sources.append(
                WorkflowSource(
                    id=raw["id"],
                    entry_path=entry_path.resolve(),
                    package_root=entry_path.parent.resolve(),
                )
            )
        return sources

    def _legacy_flows(self, root: Path) -> list[WorkflowSource]:
        entries = sorted({*root.glob("*.yaml"), *root.glob("*.yml")})
        return [
            WorkflowSource(
                id=entry.stem,
                entry_path=entry.resolve(),
                package_root=None,
                legacy=True,
            )
            for entry in entries
            if entry.name != _ENTRYPOINT
        ]
