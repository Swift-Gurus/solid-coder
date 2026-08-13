"""Defines merging a nested include into an aggregate resolution."""

from typing import Protocol

from harness.include_resolution import IncludeResolution
from harness.include_source import IncludeSource


"""
solid-name: NestedIncludeResolutionMerging
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for merging a qualified nested include into an aggregate resolution.
"""
class NestedIncludeResolutionMerging(Protocol):

    def merge(
        self,
        resolution: IncludeResolution,
        source: IncludeSource,
        nested: IncludeResolution,
    ) -> IncludeResolution: ...
