"""
solid-name: IncludeResolving
solid-category: abstraction
solid-spec: [SPEC-027]
solid-description: Contract for resolving included sub-flow references in flow steps.
"""

from __future__ import annotations

from typing import Protocol

from harness.include_resolution import IncludeResolution


class IncludeResolving(Protocol):

    def resolve(self, raw_steps: list[dict], flow_file_path: str) -> IncludeResolution: ...