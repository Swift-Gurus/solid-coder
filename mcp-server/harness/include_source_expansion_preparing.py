"""Defines preparation of nested include traversal context."""

from typing import Protocol

from harness.include_source import IncludeSource
from harness.include_traversal_context import IncludeTraversalContext


"""
solid-name: IncludeSourceExpansionPreparing
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for validating and preparing traversal context for a nested include source.
"""
class IncludeSourceExpansionPreparing(Protocol):

    def prepare(
        self,
        source: IncludeSource,
        parent: IncludeTraversalContext,
    ) -> IncludeTraversalContext: ...
