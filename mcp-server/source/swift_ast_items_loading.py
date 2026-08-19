"""Defines loading top-level Swift parser items."""

from typing import Protocol


"""
solid-name: SwiftASTItemsLoading
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for loading the ordered top-level items from one Swift parser document.
"""
class SwiftASTItemsLoading(Protocol):
    def load(self, parser_document: str) -> list[object]: ...
