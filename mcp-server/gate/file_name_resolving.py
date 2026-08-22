"""Defines file-name resolution for write-gate reporting."""

from typing import Protocol


"""
solid-name: FileNameResolving
solid-category: abstraction
solid-description: Contract for resolving a display file name from a source path.
solid-tags: [hook]
"""
class FileNameResolving(Protocol):
    def resolve(self, file_path: str) -> str: ...
