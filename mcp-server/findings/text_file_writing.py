"""Defines writing rendered text to a file."""

from pathlib import Path
from typing import Protocol


"""
solid-name: TextFileWriting
solid-category: abstraction
solid-description: Contract for writing rendered text content to a requested file path.
"""
class TextFileWriting(Protocol):
    def write(self, path: Path, content: str) -> None: ...
