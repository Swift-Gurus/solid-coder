"""Aggregates workflow search-path sources."""

from __future__ import annotations

from pathlib import Path

from harness.flow_search_path_resolving import FlowSearchPathResolving
from harness.path_filtering import PathFiltering


"""
solid-name: FlowSearchPathResolver
solid-category: service
solid-spec: [SPEC-031]
solid-description: Resolves an ordered list of eligible directories from injected project and plugin workflow search-path sources.
"""
class FlowSearchPathResolver:

    def __init__(
        self,
        sources: list[FlowSearchPathResolving],
        path_filter: PathFiltering,
    ) -> None:
        self._sources = sources
        self._path_filter = path_filter

    def resolve(self) -> list[Path]:
        candidates = [path for source in self._sources for path in source.resolve()]
        return self._path_filter.filter(candidates)
