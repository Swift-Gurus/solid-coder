"""Defines selection of reviewable entries from a patch command."""

from typing import Protocol


"""
solid-name: PatchEntrySelecting
solid-category: abstraction
solid-description: Contract for selecting reviewable file changes while excluding removals.
solid-tags: [hook]
"""
class PatchEntrySelecting(Protocol):
    def select(self, command: str) -> list[dict]: ...
