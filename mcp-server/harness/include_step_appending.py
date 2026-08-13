"""Defines appending an ordinary step to an include resolution."""

from typing import Protocol

from harness.include_resolution import IncludeResolution


"""
solid-name: IncludeStepAppending
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for appending a non-include step to an include resolution.
"""
class IncludeStepAppending(Protocol):

    def append(self, resolution: IncludeResolution, step: dict) -> IncludeResolution: ...
