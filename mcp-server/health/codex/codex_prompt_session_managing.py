"""Defines lifecycle operations for Codex prompt files."""

from pathlib import Path
from typing import Optional, Protocol


"""
solid-name: CodexPromptSessionManaging
solid-category: abstraction
solid-description: Contract for creating, opening, reading, and releasing prompt execution files.
solid-tags: [hook, llm]
"""
class CodexPromptSessionManaging(Protocol):
    def write_prompt(self, prompt: str) -> Path: ...
    def result_path(self) -> Path: ...
    def prompt_stdin(self, path: Path): ...
    def read_result(self, path: Path) -> Optional[str]: ...
    def cleanup(self, *paths: Path) -> None: ...
