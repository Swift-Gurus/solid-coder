"""Defines construction of resolved include-source models."""

from __future__ import annotations

from typing import Protocol

from harness.include_source import IncludeSource


"""
solid-name: IncludeSourceCreating
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-035]
solid-description: Contract for constructing the shared representation of a selected include source.
"""
class IncludeSourceCreating(Protocol):

    def create(
        self,
        alias: str,
        steps: list[dict],
        flow_path: str,
        identity: str | None = None,
        label: str | None = None,
        source_path: str | None = None,
        workflow_id: str | None = None,
    ) -> IncludeSource:
        ...
