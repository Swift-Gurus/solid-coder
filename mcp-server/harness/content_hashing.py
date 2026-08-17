"""Defines deterministic hashing of authored review content."""

from typing import Protocol


"""
solid-name: ContentHashing
solid-category: abstraction
solid-spec: [SPEC-039]
solid-description: Contract for producing deterministic hashes from authored byte content.
"""
class ContentHashing(Protocol):
    def hash(self, content: bytes) -> str: ...
