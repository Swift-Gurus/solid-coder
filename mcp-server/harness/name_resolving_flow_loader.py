"""
solid-name: NameResolvingFlowLoader
solid-category: service
solid-spec: [SPEC-031]
solid-description: Loads a flow definition with automatic name resolution through search paths.
"""

from __future__ import annotations

from harness.flow_file_resolving import FlowFileResolving
from harness.flow_loading import FlowLoading
from harness.models import FlowDef


class NameResolvingFlowLoader:

    def __init__(self, file_resolver: FlowFileResolving, inner_loader: FlowLoading) -> None:
        self._file_resolver = file_resolver
        self._inner_loader = inner_loader

    def load(self, path: str, search_paths: list[str]) -> FlowDef:
        resolved = self._file_resolver.resolve(path, search_paths)
        return self._inner_loader.load(resolved, search_paths)
