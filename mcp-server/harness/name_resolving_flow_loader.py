from __future__ import annotations

from harness.flow_file_resolving import FlowFileResolving
from harness.flow_loading import FlowLoading
from harness.models import FlowDef
from harness.workflow_catalog_resolving import WorkflowCatalogScoping


"""
solid-name: NameResolvingFlowLoader
solid-category: service
solid-spec: [SPEC-031]
solid-description: Loads a flow definition with automatic name resolution through search paths.
"""
class NameResolvingFlowLoader:

    def __init__(
        self,
        file_resolver: FlowFileResolving,
        inner_loader: FlowLoading,
        catalog_scope: WorkflowCatalogScoping,
    ) -> None:
        self._file_resolver = file_resolver
        self._inner_loader = inner_loader
        self._catalog_scope = catalog_scope

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        with self._catalog_scope.scope(search_paths):
            resolved = self._file_resolver.resolve(path, search_paths)
            return self._inner_loader.load(resolved, search_paths)
