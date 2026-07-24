"""
solid-name: StartupContextResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves path configuration needed to initialize flow execution.
"""

from __future__ import annotations

from harness.flow_search_path_resolving import FlowSearchPathResolving
from harness.runs_base_dir_resolving import RunsBaseDirResolving
from harness.startup_context import StartupContext


class StartupContextResolver:

    def __init__(
        self,
        base_dir_resolver: RunsBaseDirResolving,
        search_paths: FlowSearchPathResolving,
    ) -> None:
        self._base_dir_resolver = base_dir_resolver
        self._search_paths = search_paths

    def resolve(self) -> StartupContext:
        return StartupContext(
            base_dir=self._base_dir_resolver.resolve(),
            search_paths=[str(p) for p in self._search_paths.resolve()],
        )
