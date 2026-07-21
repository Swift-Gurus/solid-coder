"""
solid-name: FlowFileResolver
solid-category: service
solid-spec: [SPEC-013]
solid-description: Resolves a flow identifier to its file path, returning the original identifier if not found.
"""

from __future__ import annotations

from pathlib import Path

from harness.path_checking import PathChecking

_EXTENSIONS = (".yaml", ".yml")


class FlowFileResolver:

    def __init__(self, path_checker: PathChecking) -> None:
        self._path_checker: PathChecking = path_checker

    def resolve(self, flow: str, search_paths: list[str]) -> str:
        for directory in search_paths:
            for extension in _EXTENSIONS:
                candidate = str(Path(directory) / f"{flow}{extension}")
                if self._path_checker.exists(candidate):
                    return candidate
        return flow
