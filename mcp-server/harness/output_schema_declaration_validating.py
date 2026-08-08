"""Defines validation of an output schema declaration."""

from __future__ import annotations

from typing import Protocol


"""
solid-name: OutputSchemaDeclarationValidating
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for validating mutually exclusive inline and file-backed output schema declarations.
"""
class OutputSchemaDeclarationValidating(Protocol):
    def validate(self, step: dict, output: dict) -> None: ...
