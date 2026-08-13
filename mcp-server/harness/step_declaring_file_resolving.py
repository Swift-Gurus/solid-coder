"""Defines resolution of the workflow file that declared a step."""

from __future__ import annotations

from pathlib import Path
from typing import Protocol


"""
solid-name: StepDeclaringFileResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for resolving the workflow file that owns one expanded step declaration.
"""
class StepDeclaringFileResolving(Protocol):

    def resolve(self, source_file: str | None, flow_file_path: str) -> Path:
        ...
