"""Discovers recursively packaged workflow entrypoints below one root."""

from __future__ import annotations

from pathlib import Path

from harness.structured_model_decoding import StructuredModelDecoding
from harness.workflow_package_catalog_document import WorkflowPackageCatalogDocument
from harness.workflow_source import WorkflowSource
from harness.workflow_source_discovering import WorkflowSourceDiscovering
from scoring.yaml_config_file_loader import ConfigFileLoading

_ENTRYPOINT = "workflow.yaml"


"""
solid-name: PackageWorkflowSourceDiscoverer
solid-category: service
solid-spec: [SPEC-035, SPEC-039]
solid-description: Discovers recursive workflow packages and returns their validated typed sources.
"""
class PackageWorkflowSourceDiscoverer(WorkflowSourceDiscovering):

    def __init__(
        self,
        file_loader: ConfigFileLoading,
        document_decoder: StructuredModelDecoding[WorkflowPackageCatalogDocument],
    ) -> None:
        self._file_loader = file_loader
        self._document_decoder = document_decoder

    def discover(self, root: Path) -> list[WorkflowSource]:
        if not root.is_dir():
            return []
        sources: list[WorkflowSource] = []
        for entry_path in sorted(root.rglob(_ENTRYPOINT)):
            raw = self._file_loader.load(entry_path)
            document = self._document_decoder.decode(
                raw,
                f"workflow package '{entry_path}'",
            )
            sources.append(
                WorkflowSource(
                    id=document.id,
                    entry_path=entry_path.resolve(),
                    package_root=entry_path.parent.resolve(),
                    rule=document.rule,
                )
            )
        return sources
