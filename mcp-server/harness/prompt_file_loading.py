"""Defines validated loading of prompt file content."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: PromptFileLoading
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for loading required prompt text from a resolved workflow resource path.
"""
class PromptFileLoading(Protocol):
    def load(self, path: Path, step_id: str, reference: str) -> str: ...
