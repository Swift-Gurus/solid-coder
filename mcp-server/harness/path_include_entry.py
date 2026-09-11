"""Defines a validated path-based workflow include entry."""

from __future__ import annotations

from dataclasses import dataclass


"""
solid-name: PathIncludeEntry
solid-category: model
solid-spec: [SPEC-027, SPEC-045]
solid-description: Carries the path, alias, and declaring source of one path-based workflow include.
"""
@dataclass(frozen=True)
class PathIncludeEntry:
    path: str
    alias: str
    source_file: str | None = None
