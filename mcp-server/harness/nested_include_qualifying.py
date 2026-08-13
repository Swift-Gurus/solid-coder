"""Defines alias qualification of a nested include resolution."""

from typing import Protocol

from harness.include_resolution import IncludeResolution


"""
solid-name: NestedIncludeQualifying
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for qualifying nested workflow steps and groups under their owning alias.
"""
class NestedIncludeQualifying(Protocol):

    def qualify(self, alias: str, nested: IncludeResolution) -> IncludeResolution: ...
