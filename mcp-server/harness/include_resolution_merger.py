"""Coordinates include-resolution assembly operations."""

from harness.include_resolution import IncludeResolution
from harness.include_resolution_merging import IncludeResolutionMerging
from harness.include_source import IncludeSource
from harness.include_step_appending import IncludeStepAppending
from harness.nested_include_resolution_merging import NestedIncludeResolutionMerging


"""
solid-name: IncludeResolutionMerger
solid-category: service
solid-spec: [SPEC-027, SPEC-035]
solid-description: Coordinates construction of recursive include-resolution results.
"""
class IncludeResolutionMerger(IncludeResolutionMerging):

    def __init__(
        self,
        step_appender: IncludeStepAppending,
        nested_merger: NestedIncludeResolutionMerging,
    ) -> None:
        self._step_appender = step_appender
        self._nested_merger = nested_merger

    def append_step(
        self,
        resolution: IncludeResolution,
        step: dict,
    ) -> IncludeResolution:
        return self._step_appender.append(resolution, step)

    def merge(
        self,
        resolution: IncludeResolution,
        source: IncludeSource,
        nested: IncludeResolution,
    ) -> IncludeResolution:
        return self._nested_merger.merge(resolution, source, nested)
