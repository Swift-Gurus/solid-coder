"""
solid-name: RunsBaseDirResolver
solid-category: service
solid-spec: [SPEC-031]
solid-description: Resolves the base directory path where flow runs are stored for the current project.
"""

from __future__ import annotations

from pathlib import Path
from typing import Callable, Optional

from harness.runs_base_dir_resolving import RunsBaseDirResolving
from hook_utils import solid_coder_project_dir


class RunsBaseDirResolver:

    def __init__(self, project_dir_fn: Optional[Callable[[], Path]] = None) -> None:
        self._project_dir_fn: Callable[[], Path] = project_dir_fn or solid_coder_project_dir

    def resolve(self) -> Path:
        return self._project_dir_fn() / "runs"
