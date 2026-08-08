"""Defines resolution of a prompt file reference."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: PromptFilePathResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for resolving a step prompt-file reference from its declaring workflow file.
"""
class PromptFilePathResolving(Protocol):
    def resolve(self, step: dict, flow_file_path: str, prompt_file: str) -> Path: ...
