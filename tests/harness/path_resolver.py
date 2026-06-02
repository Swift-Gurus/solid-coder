"""
solid-name: PathResolver
solid-category: utility
solid-spec: [SPEC-014]
solid-description: Resolves a path reference to its corresponding test directory within the project.
"""

from __future__ import annotations

import sys
from pathlib import Path

_HARNESS_DIR = Path(__file__).resolve().parent
if str(_HARNESS_DIR) not in sys.path:
    sys.path.insert(0, str(_HARNESS_DIR))

from interfaces import PathResolving  # noqa: E402

_REFERENCES_PREFIX = "references/"


class PathResolver(PathResolving):
    def __init__(self, project_root: Path) -> None:
        self._project_root = project_root

    def resolve(self, references_path: str) -> Path:
        normalized = references_path.replace("\\", "/")
        if normalized.startswith(_REFERENCES_PREFIX):
            suffix = normalized[len(_REFERENCES_PREFIX):]
        else:
            suffix = normalized
        resolved = self._project_root / "tests" / suffix
        if not resolved.exists():
            raise ValueError(f"Tests directory does not exist: {resolved}")
        return resolved
