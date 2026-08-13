"""Defines recursive traversal of workflow include sources."""

from typing import Protocol

from harness.include_resolution import IncludeResolution
from harness.include_traversal_context import IncludeTraversalContext


"""
solid-name: IncludeTraversing
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for recursively traversing and expanding workflow include sources.
"""
class IncludeTraversing(Protocol):

    def traverse(
        self,
        raw_steps: list[dict],
        search_paths: list[str],
        context: IncludeTraversalContext,
    ) -> IncludeResolution: ...
