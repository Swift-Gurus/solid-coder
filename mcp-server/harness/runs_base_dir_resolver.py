"""
solid-name: RunsBaseDirResolver
solid-category: service
solid-spec: [SPEC-031]
solid-description: Resolves the base directory path where flow runs are stored for the current project.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

from hook_utils import solid_coder_project_dir


class RunsBaseDirResolver:
    def __init__(self, project_dir_fn: Callable[[], Path] | None = None) -> None:
        self._project_dir_fn: Callable[[], Path] = (
            project_dir_fn or solid_coder_project_dir
        )

    def resolve(self) -> Path:
        return self._project_dir_fn() / "runs"
