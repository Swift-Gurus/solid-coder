"""Adapts path-backed source content to exact bytes."""

from pathlib import Path

from source.source_bytes_reading import SourceBytesReading


"""
solid-name: PathSourceBytesReader
solid-category: adapter
solid-spec: [SPEC-040]
solid-description: Reads exact source bytes from one supplied filesystem path.
"""
class PathSourceBytesReader(SourceBytesReading):
    """Boundary adapter around the standard-library path read API."""

    def read(self, path: Path) -> bytes:
        return path.read_bytes()
