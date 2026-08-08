"""Defines construction of Codex execution commands."""

from pathlib import Path
from typing import Protocol


"""
solid-name: CodexCommandBuilding
solid-category: abstraction
solid-description: Contract for constructing an executable command for a result destination.
solid-tags: [hook, llm]
"""
class CodexCommandBuilding(Protocol):
    def build(self, result_path: Path) -> list[str]: ...
