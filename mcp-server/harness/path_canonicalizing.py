"""Defines canonicalization of filesystem path strings."""

from typing import Protocol


"""
solid-name: PathCanonicalizing
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for converting a filesystem path string to its canonical absolute form.
"""
class PathCanonicalizing(Protocol):

    def canonicalize(self, path: str) -> str: ...
