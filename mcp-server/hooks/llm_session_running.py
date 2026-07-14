"""
solid-description: Contract for executing a prompt and returning the result.
solid-category: abstraction
solid-tags: [hook]
"""

from typing import Optional, Protocol


class LlmSessionRunning(Protocol):
    """Runs a prompt through the configured LLM backend and returns corrected content or None."""

    def run(self, prompt: str, cwd: str = "") -> Optional[str]: ...