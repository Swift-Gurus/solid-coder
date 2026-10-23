"""Defines managed use of prompt execution artifacts."""

from collections.abc import Callable
from pathlib import Path
from typing import Protocol

"""
solid-name: CodexPromptArtifactUsing
solid-category: abstraction
solid-description: Contract for running an operation with managed prompt and result artifacts.
solid-tags: [hook, llm]
"""


class CodexPromptArtifactUsing(Protocol):
    def use(
        self,
        prompt: str,
        operation: Callable[[object, Path], None],
    ) -> str | None: ...
