"""Defines resolution of one file-backed output schema declaration."""

from pathlib import Path
from typing import Protocol


"""
solid-name: OutputSchemaReferenceResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for validating and resolving one output schema declaration from its owning workflow file.
"""
class OutputSchemaReferenceResolving(Protocol):

    def resolve(self, step: dict, output: dict, declaring_file: Path) -> dict:
        ...
