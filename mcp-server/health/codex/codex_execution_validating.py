"""Defines validation of completed Codex subprocess executions."""

from typing import Protocol


"""
solid-name: CodexExecutionValidating
solid-category: abstraction
solid-description: Contract for validating a completed Codex execution outcome.
solid-tags: [hook, llm]
"""
class CodexExecutionValidating(Protocol):
    def validate(self, succeeded: bool, stdout: str, stderr: str) -> None: ...
