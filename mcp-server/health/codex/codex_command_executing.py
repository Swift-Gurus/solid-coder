"""Defines validated execution of Codex commands."""

from typing import Protocol


"""
solid-name: CodexCommandExecuting
solid-category: abstraction
solid-description: Contract for executing and validating a Codex command with configured process input.
solid-tags: [hook, llm]
"""
class CodexCommandExecuting(Protocol):
    def execute(
        self,
        command: list[str],
        timeout: int,
        stdin: object,
        cwd: str,
    ) -> None: ...
