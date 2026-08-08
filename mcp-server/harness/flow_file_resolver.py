"""
solid-name: FlowFileResolver
solid-category: service
solid-spec: [SPEC-031]
solid-description: Resolves a flow identifier to its file path, returning the original identifier if not found.
"""

from __future__ import annotations

from pathlib import Path

from harness.path_checking import PathChecking
from harness.workflow_catalog_resolving import WorkflowCatalogResolving


class FlowFileResolver:

    def __init__(
        self,
        path_checker: PathChecking,
        catalog_resolver: WorkflowCatalogResolving,
    ) -> None:
        self._path_checker: PathChecking = path_checker
        self._catalog_resolver = catalog_resolver

    def resolve(self, flow: str, search_paths: list[str]) -> str:
        if self._path_checker.exists(flow):
            return flow
        source = self._catalog_resolver.resolve(flow, search_paths)
        if source is not None:
            return str(source.entry_path)
        return flow
