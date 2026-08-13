"""Defines assembly of recursive include-resolution results."""

from typing import Protocol

from harness.include_resolution import IncludeResolution
from harness.include_source import IncludeSource


"""
solid-name: IncludeResolutionMerging
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for assembling expanded steps and include provenance into one resolution.
"""
class IncludeResolutionMerging(Protocol):

    def append_step(
        self,
        resolution: IncludeResolution,
        step: dict,
    ) -> IncludeResolution: ...

    def merge(
        self,
        resolution: IncludeResolution,
        source: IncludeSource,
        nested: IncludeResolution,
    ) -> IncludeResolution: ...
