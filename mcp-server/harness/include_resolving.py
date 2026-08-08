"""Defines recursive expansion of workflow includes and inline groups."""

from __future__ import annotations

from typing import Protocol

from harness.include_resolution import IncludeResolution


"""
solid-name: IncludeResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for resolving included sub-flow references in flow steps.
"""
class IncludeResolving(Protocol):

    def resolve(
        self,
        raw_steps: list[dict],
        flow_file_path: str,
        search_paths: list[str] | None = None,
        root_workflow_id: str | None = None,
    ) -> IncludeResolution: ...
