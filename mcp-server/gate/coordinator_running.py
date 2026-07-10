"""
solid-description: Contract that defines execution behavior for tool-driven operations.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Protocol


class CoordinatorRunning(Protocol):
    def run(self, tool_name: str, tool_input: dict, file_path: str, language: str, session_id: str, cwd: str) -> None: ...