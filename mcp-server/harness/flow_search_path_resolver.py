"""
solid-name: FlowSearchPathResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves an ordered list of directories to search for flow files.
"""

from __future__ import annotations

from pathlib import Path

from harness.env_reading import EnvReading
from harness.flow_search_path_resolving import FlowSearchPathResolving
from harness.os_env_reader import OsEnvReader
from harness.path_checking import PathChecking, PathChecker

_PLUGIN_FLOWS = Path(__file__).resolve().parents[1] / "harness" / "flows"


class FlowSearchPathResolver:

    def __init__(
        self,
        env: EnvReading | None = None,
        path_checker: PathChecking | None = None,
    ) -> None:
        self._env: EnvReading = env or OsEnvReader()
        self._path_checker: PathChecking = path_checker or PathChecker()

    def resolve(self) -> list[Path]:
        paths: list[Path] = []

        project_dir = self._env.get("CLAUDE_PROJECT_DIR")
        if project_dir:
            project_flows = Path(project_dir) / ".solid-coder" / "harness" / "flows"
            if self._path_checker.exists(str(project_flows)):
                paths.append(project_flows)

        if self._path_checker.exists(str(_PLUGIN_FLOWS)):
            paths.append(_PLUGIN_FLOWS)

        return paths
