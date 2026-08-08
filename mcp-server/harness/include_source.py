"""Defines one resolved source of an include or inline group entry."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: IncludeSource
solid-category: model
solid-spec: [SPEC-027, SPEC-035]
solid-description: Carries the steps, identity, location, and provenance selected for one include entry.
"""
@dataclass(frozen=True)
class IncludeSource:
    alias: str
    steps: list[dict]
    flow_path: str
    identity: str | None = None
    label: str | None = None
    source_path: str | None = None
    workflow_id: str | None = None
