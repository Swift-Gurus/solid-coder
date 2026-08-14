"""Defines retrieval of specification ancestry."""

from typing import Protocol


"""
solid-name: SpecAncestryRetrieving
solid-category: abstraction
solid-description: Contract for retrieving ancestry records for one specification.
"""
class SpecAncestryRetrieving(Protocol):
    def retrieve(self, spec_number: str, blocked: bool) -> list[dict]: ...
