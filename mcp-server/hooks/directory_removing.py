"""Defines recursive directory removal."""

from typing import Protocol


"""
solid-name: DirectoryRemoving
solid-category: abstraction
solid-description: Contract for removing an output directory and its contents with optional filesystem-error suppression.
"""
class DirectoryRemoving(Protocol):
    def __call__(self, path: str, *, ignore_errors: bool = False) -> None: ...
