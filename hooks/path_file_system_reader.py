"""
solid-description: Wraps Path filesystem operations behind a protocol for injection and testing.
solid-category: service
solid-tags: [hook, utility]
"""

from pathlib import Path
from typing import Protocol


class FileSystemReading(Protocol):
    """Protocol for filesystem access — lets ViolationExtractor be tested without real disk I/O."""

    def glob(self, directory: str, pattern: str) -> list: ...
    def read_text(self, path: object, encoding: str = "utf-8") -> str: ...
    def is_dir(self, path: str) -> bool: ...
    def subpath(self, directory: str, name: str) -> str: ...


class PathFileSystemReader:
    """Boundary adapter: wraps Path filesystem operations for injection.

    Path is a stdlib class (not developer-owned) — this satisfies the
    OCP Boundary Adapter exception.
    """

    def glob(self, directory: str, pattern: str) -> list:
        return list(Path(directory).glob(pattern))

    def read_text(self, path: object, encoding: str = "utf-8") -> str:
        return Path(str(path)).read_text(encoding=encoding)

    def is_dir(self, path: str) -> bool:
        return Path(path).is_dir()

    def subpath(self, directory: str, name: str) -> str:
        return str(Path(directory) / name)
