"""Structural error-evidence contract implemented by parser nodes."""

from typing import Protocol

from tree_sitter import Point


"""
solid-name: SyntaxDiagnosticNodeReading
solid-category: abstraction
solid-spec: [SPEC-063]
solid-description: Contract for reading syntax error flags, node kind and source position when producing recoverable diagnostics.
"""
class SyntaxDiagnosticNodeReading(Protocol):
    @property
    def is_error(self) -> bool: ...

    @property
    def is_missing(self) -> bool: ...

    @property
    def has_error(self) -> bool: ...

    @property
    def child_count(self) -> int: ...

    @property
    def type(self) -> str: ...

    @property
    def start_point(self) -> Point: ...
