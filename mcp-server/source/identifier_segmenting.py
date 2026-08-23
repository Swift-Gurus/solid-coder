"""Defines deterministic segmentation of source identifiers into lexical parts."""

from typing import Protocol


"""
solid-name: IdentifierSegmenting
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for dividing source identifiers into ordered lexical components.
"""
class IdentifierSegmenting(Protocol):
    def segment(self, identifier: str) -> list[str]: ...
