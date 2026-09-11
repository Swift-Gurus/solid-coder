"""Defines typed recognition of path-based workflow include entries."""

from __future__ import annotations

from collections.abc import Mapping
from typing import Protocol

from harness.path_include_entry import PathIncludeEntry


"""
solid-name: PathIncludeEntryReading
solid-category: abstraction
solid-spec: [SPEC-027, SPEC-045]
solid-description: Contract for recognizing and validating a path-based include at the structured-input boundary.
"""
class PathIncludeEntryReading(Protocol):
    def read(self, raw: Mapping[str, object]) -> PathIncludeEntry | None: ...
