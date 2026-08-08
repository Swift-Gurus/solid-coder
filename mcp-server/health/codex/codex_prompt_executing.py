"""Defines execution of prompts through Codex."""

from typing import Optional, Protocol


"""
solid-name: CodexPromptExecuting
solid-category: abstraction
solid-description: Contract for executing a prompt and returning its final response.
solid-tags: [hook, llm]
"""
class CodexPromptExecuting(Protocol):
    def execute(self, prompt: str, timeout: int) -> Optional[str]: ...
