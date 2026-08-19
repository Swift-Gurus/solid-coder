"""Defines qualification of structured Swift view declarations."""

from typing import Protocol


"""
solid-name: SwiftViewDeclarationQualifying
solid-category: abstraction
solid-spec: [SPEC-040]
solid-description: Contract for identifying view declarations in structured Swift parser items.
"""
class SwiftViewDeclarationQualifying(Protocol):

    def qualifies(self, item: object) -> bool: ...
