"""
solid-name: StartupContextResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves environment and path configuration needed to initialize flow execution.
"""

from __future__ import annotations

from harness.env_detecting import EnvDetecting
from harness.flow_search_path_resolving import FlowSearchPathResolving
from harness.runs_base_dir_resolving import RunsBaseDirResolving
from harness.startup_context import StartupContext


class StartupContextResolver:

    def __init__(
        self,
        env_detector: EnvDetecting,
        base_dir_resolver: RunsBaseDirResolving,
        search_paths: FlowSearchPathResolving,
    ) -> None:
        self._env_detector = env_detector
        self._base_dir_resolver = base_dir_resolver
        self._search_paths = search_paths

    def resolve(self) -> StartupContext:
        return StartupContext(
            detected_env=self._env_detector.detect(),
            base_dir=self._base_dir_resolver.resolve(),
            search_paths=[str(p) for p in self._search_paths.resolve()],
        )