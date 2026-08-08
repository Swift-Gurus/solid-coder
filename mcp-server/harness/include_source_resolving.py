"""Defines selection of a source for one include or inline-group entry."""

from __future__ import annotations

from typing import Protocol

from harness.include_source import IncludeSource


"""
solid-name: IncludeSourceResolving
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for selecting the steps and provenance represented by one include entry.
"""
class IncludeSourceResolving(Protocol):

    def resolve(
        self,
        entry: dict,
        flow_file_path: str,
        search_paths: list[str],
    ) -> IncludeSource | None:
        ...
