"""Canonicalizes filesystem path strings."""

from harness.path_building import PathBuilding
from harness.path_canonicalizing import PathCanonicalizing


"""
solid-name: PathCanonicalizer
solid-category: adapter
solid-spec: [SPEC-027, SPEC-035]
solid-description: Converts filesystem path strings to canonical absolute paths.
"""
class PathCanonicalizer(PathCanonicalizing):

    def __init__(self, path_builder: PathBuilding) -> None:
        self._path_builder = path_builder

    def canonicalize(self, path: str) -> str:
        return str(self._path_builder.build(path))
