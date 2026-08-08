"""Defines parsing and content transformation for apply_patch entries."""

from typing import Protocol


"""
solid-name: PatchParsing
solid-category: abstraction
solid-description: Contract for parsing patch entries and applying their add or update content transformations.
solid-tags: [hook]
"""
class PatchParsing(Protocol):
    def parse(self, command: str) -> list: ...
    def add_content(self, lines: list) -> str: ...
    def apply_update(self, existing_content: str, body_lines: list) -> str: ...
